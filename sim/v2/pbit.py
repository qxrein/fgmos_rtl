"""
p-bit configuration of the QFG primitive (transistor level, Sky130 BSIM4).

Configuration: FG receives Nw weighted inputs (W0..), one noise-coupling input
NZ and the reset bias VB.  The decision stage is the same ratioed PMOS-load
stage with a single clocked pull-down (EN), followed by the restoring inverter:
    m = [ V_FG > V* ],  V_FG = VB + sum_j k_j*VDD*m_j + k_n*xi + q_kTC
Each reset/evaluate cycle is one p-bit update with a fresh noise sample xi.

Functions here:
  sigmoid_run(...)   transistor-level P(m=1) vs VB with injected Gaussian xi
  noise_ktc(...)     ngspice .noise: integrated reset (kT/C) noise on FG
  noise_comp(...)    ngspice .noise: input-referred noise of the decision stage
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ngs import DEFAULT, VDD, header, parse_kv, run

PB_DEFAULT = dict(DEFAULT)
PB_DEFAULT.update(dict(wen=0.42, len_=0.15, cnw=3.0, cnl=3.0))


def pbit_subckt(p=None, Nw=2, name="QFG_PB"):
    q = dict(PB_DEFAULT)
    if p:
        q.update(p)
    ws = [f"W{i}" for i in range(Nw)]
    L = [f".subckt {name} {' '.join(ws)} NZ EN RST VB Y YB FG VDD VSS",
         f"XMP  YB FG VDD VDD sky130_fd_pr__pfet_01v8 W={q['wp']} L={q['lp']}",
         f"XMEN YB EN VSS VSS sky130_fd_pr__nfet_01v8 W={q['wen']} L={q['len_']}"]
    for w in ws:
        L.append(f"XC{w} FG {w} sky130_fd_pr__cap_mim_m3_1 W={q['cw']} L={q['cl']} MF=1")
    L += [f"XCN FG NZ sky130_fd_pr__cap_mim_m3_1 W={q['cnw']} L={q['cnl']} MF=1",
          f"XCBL FG VSS sky130_fd_pr__cap_mim_m3_1 W={q['bw']} L={q['bl']} MF=1",
          f"XMR  FG RST VB VSS sky130_fd_pr__nfet_01v8 W={q['wr']} L={q['lr']}",
          f"XIP  Y  YB VDD VDD sky130_fd_pr__pfet_01v8 W={q['wip']} L=0.15",
          f"XIN  Y  YB VSS VSS sky130_fd_pr__nfet_01v8 W={q['win']} L=0.15",
          f".ends {name}"]
    return "\n" + "\n".join(L) + "\n"


T_R, T_E, EDGE = 1.0, 2.0, 0.05


def _cycles(xi, vdd, wbits):
    """PWL strings for RST, EN, NZ and weight inputs for len(xi) cycles."""
    tc = T_R + T_E
    rst, en, nz = [(0, vdd)], [(0, 0)], [(0, 0)]
    w = [[(0, 0)] for _ in wbits]
    for k, x in enumerate(xi):
        t0 = k * tc
        rst += [(t0 + T_R, vdd), (t0 + T_R + EDGE, 0), (t0 + tc - EDGE, 0), (t0 + tc, vdd)]
        ts = t0 + T_R + 2 * EDGE
        nz += [(ts, 0), (ts + EDGE, x), (t0 + tc - 2 * EDGE, x), (t0 + tc - EDGE, 0)]
        en += [(ts + 2 * EDGE, 0), (ts + 3 * EDGE, vdd), (t0 + tc - 2 * EDGE, vdd), (t0 + tc - EDGE, 0)]
        for lst, b in zip(w, wbits):
            v = vdd * b
            lst += [(ts, 0), (ts + EDGE, v), (t0 + tc - 2 * EDGE, v), (t0 + tc - EDGE, 0)]
    f = lambda pts: "PWL(" + " ".join(f"{t:.4f}n {v:.5f}" for t, v in pts) + ")"
    return f(rst), f(en), f(nz), [f(x) for x in w], len(xi) * tc


def sigmoid_run(vb, sigma_xi, n_cyc=300, p=None, corner="tt", temp=27.0, vdd=VDD,
                seed=0, wbits=(0, 0), mc=False, mc_seed=None, tag="pbsig"):
    rng = np.random.default_rng(seed)
    xi = rng.normal(0.0, sigma_xi, n_cyc)
    rst, en, nz, ws, tstop = _cycles(xi, vdd, wbits)
    tc = T_R + T_E
    meas, echo = [], []
    for k in range(n_cyc):
        ts = k * tc + tc - 3 * EDGE
        meas.append(f"meas tran y{k} FIND v(y) AT={ts:.4f}n")
        meas.append(f"meas tran f{k} FIND v(fg) AT={ts:.4f}n")
    # write results in chunks to keep echo lines short
    chunks = []
    for c0 in range(0, n_cyc, 25):
        items = " ".join(f"y{k}=$&y{k} f{k}=$&f{k}" for k in range(c0, min(n_cyc, c0 + 25)))
        chunks.append(f'echo "{items}" >> out.txt')
    wsrc = "\n".join(f"Vw{i} w{i} 0 {s}" for i, s in enumerate(ws))
    wnodes = " ".join(f"w{i}" for i in range(len(ws)))
    seed_line = f"set rndseed={mc_seed}" if mc_seed is not None else ""
    deck = header(corner, temp, mc) + pbit_subckt(p, Nw=len(ws)) + f"""
Vdd vdd 0 {vdd}
Vrst rst 0 {rst}
Ven en 0 {en}
Vnz nz 0 {nz}
Vvb vb 0 {vb}
{wsrc}
X1 {wnodes} nz en rst vb y yb fg vdd 0 QFG_PB
CL y 0 5f
.option method=gear reltol=1e-4
.control
{seed_line}
tran 10p {tstop}n
{chr(10).join(meas)}
{chr(10).join(chunks)}
.endc
.end
"""
    _, d = run(deck, tag=tag)
    kv = {}
    for r in parse_kv(d / "out.txt"):
        kv.update(r)
    y = np.array([kv[f"y{k}"] for k in range(n_cyc)])
    f = np.array([kv[f"f{k}"] for k in range(n_cyc)])
    return pd.DataFrame({"xi": xi, "y": y, "fg": f, "bit": (y > vdd / 2).astype(int)})


def noise_ktc(p=None, corner="tt", temp=27.0, vdd=VDD, vb=0.5, Nw=2):
    """Integrated noise on FG while the reset switch is ON (should be ~sqrt(kT/C_FG))."""
    deck = header(corner, temp) + pbit_subckt(p, Nw=Nw) + f"""
Vdd vdd 0 {vdd}
Vrst rst 0 {vdd}
Ven en 0 0
Vnz nz 0 0
Vvb vb 0 DC {vb} AC 1
{chr(10).join(f'Vw{i} w{i} 0 0' for i in range(Nw))}
X1 {' '.join(f'w{i}' for i in range(Nw))} nz en rst vb y yb fg vdd 0 QFG_PB
.control
noise v(fg) Vvb dec 50 1 1e13
setplot noise2
let vn = sqrt(onoise_total^2)
echo "vn_fg=$&vn" > out.txt
.endc
.end
"""
    _, d = run(deck, tag="ktc")
    return parse_kv(d / "out.txt")[0]["vn_fg"]


def noise_comp(vfg_trip, p=None, corner="tt", temp=27.0, vdd=VDD, Nw=2):
    """Input-referred (FG-referred) integrated noise of the decision stage at its trip point."""
    deck = header(corner, temp) + pbit_subckt(p, Nw=Nw).replace(
        "XMR  FG RST VB VSS", "*XMR FG RST VB VSS") + f"""
Vdd vdd 0 {vdd}
Ven en 0 {vdd}
Vfg fg 0 DC {vfg_trip} AC 1
X1 {' '.join('0' for _ in range(Nw))} 0 en 0 0 y yb fg vdd 0 QFG_PB
.control
noise v(yb) Vfg dec 50 1 1e12
setplot noise2
echo "vin=$&inoise_total von=$&onoise_total" > out.txt
.endc
.end
"""
    _, d = run(deck, tag="ncomp")
    return parse_kv(d / "out.txt")[0]
