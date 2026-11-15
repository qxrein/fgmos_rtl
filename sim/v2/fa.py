"""
Cascaded threshold-logic full adder built from two QFG cells (transistor level, Sky130 BSIM4).

  cell 1 (K=3, MAJ3):           Cout = [A+B+C >= 2]
  buffer (2 inverters) on Y_B1:  NC = not Cout (high during reset, because Y_B1 precharges high)
  cell 2 (K=5):                 Sum  = [A+B+C+2*NC >= 3]  = A xor B xor C

NC is high while cell 2 is reset, so when it falls during evaluation it removes 2*Delta from FG2:
inputs that are high during reset realise negative weights. The FG2 reference therefore includes
2*Delta, which the programming voltage V_B2 absorbs. Inputs A, B, C are return-to-zero pulses
shared by both cells.

Per corner: transient sweep of V_B2 (V_B1 at the MAJ3 replica value) -> window in which both outputs
are correct for all eight minterms; then waveforms, delay and energy at the window centre.
Delays are settling times (the output stays on its final side of VDD/2 afterwards), so the
sum glitch for inputs with a carry is included.  `--timing-only` reuses fa_window.csv.
Writes data/v2/fa_window.csv, fa_timing.csv, fa_wave_<corner>.txt
"""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

import tbseq
from kscale import sizing
from ngs import DATA, cell_subckt, header, parse_kv, run
from tb import MINTERMS

T_P = 0.6
COUT = "".join(str(int(a + b + c >= 2)) for a, b, c in MINTERMS)
SUM = "".join(str((a + b + c) % 2) for a, b, c in MINTERMS)
CORNERS = {"tt": (27, 1.80), "ss": (100, 1.60), "ff": (-40, 1.95), "sf": (27, 1.80), "fs": (27, 1.80)}
VB1 = pd.read_csv(DATA / "signoff2_vb.csv").set_index("corner")["vb_MAJ"].to_dict()
P5, _ = sizing(5, 0.7, 32.0)


def deck(corner, vb1, vb2_list, wave=False, t_p=None):
    global T_P
    T_P = t_p or T_P
    temp, vdd = CORNERS[corner]
    rst, a, b, c, tstop = tbseq._pwl_inputs(vdd, t_p=T_P)
    tc = tbseq.T_R + tbseq.T_E
    meas, echo = [], ["vb2=$vbv"]
    for k in range(8):
        ts = k * tc + tbseq.T_R + 3 * tbseq.T_EDGE + T_P - 0.03
        meas += [f"meas tran c{k} FIND v(y1) AT={ts:.4f}n", f"meas tran s{k} FIND v(y2) AT={ts:.4f}n"]
        echo += [f"c{k}=$&c{k}", f"s{k}=$&s{k}"]
    meas.append(f"meas tran q INTEG i(Vdd) FROM=0 TO={tstop}n")
    echo.append("q=$&q")
    wv = "  wrdata wave.txt v(a) v(b) v(c) v(nc) v(fg2) v(y1) v(y2) i(Vdd)\n" if wave else ""
    inv = lambda nm, i, o: (f"XP{nm} {o} {i} vdd vdd sky130_fd_pr__pfet_01v8 W=1.0 L=0.15\n"
                            f"XN{nm} {o} {i} 0 0 sky130_fd_pr__nfet_01v8 W=0.42 L=0.15\n")
    return header(corner, temp) + cell_subckt() + cell_subckt(P5, K=5) + f"""
Vdd vdd 0 {vdd}
Vrst rst 0 {rst}
Va a 0 {a}
Vb b 0 {b}
Vc c 0 {c}
Vvb1 vb1 0 {vb1}
Vvb2 vb2 0 0.5
X1 a b c rst vb1 y1 yb1 fg1 vdd 0 QFG_TLG
{inv('1', 'yb1', 'nbx')}{inv('2', 'nbx', 'nc')}X2 a b c nc nc rst vb2 y2 yb2 fg2 vdd 0 QFG_TLG5
CL1 y1 0 5f
CL2 y2 0 5f
.option method=gear reltol=1e-4
.control
set wr_singlescale
set wr_vecnames
foreach vbv {' '.join(f'{v:.4f}' for v in vb2_list)}
  alter Vvb2 dc = $vbv
  tran 10p {tstop}n
{chr(10).join('  ' + m for m in meas)}
  echo "{' '.join(echo)}" >> out.txt
{wv}  destroy all
end
.endc
.end
"""


def truths(r, vdd):
    c = "".join(str(int(r[f"c{k}"] > vdd / 2)) for k in range(8))
    s = "".join(str(int(r[f"s{k}"] > vdd / 2)) for k in range(8))
    return c, s


def sweep(corner):
    temp, vdd = CORNERS[corner]
    vbs = np.round(np.arange(0.0, 1.25 + 1e-9, 0.02), 4)
    chunks = [vbs[i::4] for i in range(4)]
    rows = []
    for ch in chunks:
        _, d = run(deck(corner, VB1[corner], ch), tag=f"fa_{corner}")
        for r in parse_kv(d / "out.txt"):
            co, su = truths(r, vdd)
            rows.append(dict(corner=corner, vb2=r["vb2"], cout=co, sum=su, ok=(co == COUT and su == SUM)))
    return rows


def timing_at(args):
    global T_P
    T_P = 0.6
    corner, vb2 = args
    temp, vdd = CORNERS[corner]
    _, d = run(deck(corner, VB1[corner], [vb2], wave=True), tag=f"fat_{corner}")
    r = parse_kv(d / "out.txt")[0]
    co, su = truths(r, vdd)
    a = np.loadtxt(d / "wave.txt", skiprows=1)
    t = a[:, 0]; y2 = a[:, 7]; y1 = a[:, 6]; idd = a[:, 8]
    tc = (tbseq.T_R + tbseq.T_E) * 1e-9
    dl_s, dl_c, glitch = [], [], 0
    for k in range(8):
        t_in = k * tc + (tbseq.T_R + 2.5 * tbseq.T_EDGE) * 1e-9
        t_end = t_in + T_P * 1e-9
        m = (t >= t_in) & (t <= t_end)
        for y, lst, is_sum in ((y2, dl_s, True), (y1, dl_c, False)):
            yy, tt = y[m], t[m]
            fin = yy[-1] > vdd / 2
            bad = np.where((yy > vdd / 2) != fin)[0]
            # settling time: after this instant the output stays on its final side of VDD/2
            lst.append((tt[bad[-1] + 1] - t_in) * 1e12 if len(bad) else 0.0)
            if is_sum and not fin and yy.max() > vdd / 2:
                glitch += 1
    E = -vdd * np.trapezoid(idd, t) / 8 * 1e15
    np.savetxt(DATA / f"fa_wave_{corner}.txt", a, header="t a b c nc fg2 y1 y2 i_vdd")
    return dict(corner=corner, vb2=vb2, cout=co, sum=su, ok=(co == COUT and su == SUM),
                tpd_sum_ps=max(dl_s), tpd_cout_ps=max(dl_c), sum_glitches=glitch, E_fJ_per_add=E)


if __name__ == "__main__" and "--timing-only" in sys.argv:
    W = pd.read_csv(DATA / "fa_window.csv")
    centres = {c: round(float((g[g.ok].vb2.min() + g[g.ok].vb2.max()) / 2), 4) for c, g in W.groupby("corner")}
    with Pool(5) as p:
        T = pd.DataFrame(p.map(timing_at, list(centres.items())))
    T.to_csv(DATA / "fa_timing.csv", index=False)
    print(T.round(2).to_string())
elif __name__ == "__main__":
    with Pool(5) as p:
        res = p.map(sweep, list(CORNERS))
    W = pd.DataFrame([r for rr in res for r in rr]).sort_values(["corner", "vb2"])
    W.to_csv(DATA / "fa_window.csv", index=False)
    centres = {}
    for c, g in W.groupby("corner"):
        v = g[g.ok].vb2.to_numpy()
        print(c, "window", (v.min(), v.max()) if len(v) else None)
        if len(v):
            centres[c] = round(float((v.min() + v.max()) / 2), 4)
    with Pool(5) as p:
        T = pd.DataFrame(p.map(timing_at, list(centres.items())))
    T.to_csv(DATA / "fa_timing.csv", index=False)
    print(T.round(2).to_string())
