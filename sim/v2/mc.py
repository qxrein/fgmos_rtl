"""
Mismatch Monte Carlo of the final v2 cell (Sky130 mismatch models, mc_mm_switch=1).

Per sample (one ngspice process => one mismatch draw shared by all analyses):
  1. DC trip points V_trip,n (n = 1,2,3 pull-downs on) with the reset switch ON,
     so the FG equals VB and is swept directly.
  2. Sequential transient (reset -> evaluate, all 8 minterms) at the three
     replica-referenced bias points, which gives the truth table, the FG
     coupling step and the supply charge.
Usage: python mc.py N [corner temp vdd vb_and vb_maj vb_or]
"""
from __future__ import annotations

import sys
from multiprocessing import Pool

import numpy as np
import pandas as pd

from ngs import DATA, VDD, cell_subckt, header, parse_kv, run
from tbseq import T_E, T_R, _pwl_inputs, truth


def deck(seed, corner, temp, vdd, vbs):
    rst, a, b, c, tstop = _pwl_inputs(vdd)
    tcyc = T_R + T_E
    meas, echo = [], ["vb=$vbv"]
    for k in range(8):
        ts = k * tcyc + T_R + T_E - 0.2
        meas += [f"meas tran y{k}v FIND v(y) AT={ts:.4f}n", f"meas tran fg{k}v FIND v(fg) AT={ts:.4f}n"]
        echo += [f"y{k}=$&y{k}v", f"fg{k}=$&fg{k}v"]
    meas += [f"meas tran qv INTEG i(Vdd) FROM=0 TO={tstop}n"]
    echo += ["q=$&qv"]
    vb_list = " ".join(f"{v:.4f}" for v in vbs)
    return header(corner, temp, mc=True, seed=seed) + cell_subckt() + f"""
Vdd vdd 0 {vdd}
Vrst rst 0 {rst}
Vap ap 0 {a}
Vbp bp 0 {b}
Vcp cp 0 {c}
* DC offsets used only for the trip-point DC analyses (0 V during transient)
Vao a ap 0
Vbo b bp 0
Vco c cp 0
Vvb vb 0 0.5
X1 a b c rst vb y yb fg vdd 0 QFG_TLG
CL y 0 5f
.option method=gear reltol=1e-4
.control
* ---- DC trip points (RST is high at t=0, so FG follows VB) ----
alter Vao dc = {vdd}
dc Vvb -0.3 1.25 0.001
meas dc vt1 WHEN v(yb)={vdd/2} CROSS=1
set s1 = "$&vt1"
alter Vbo dc = {vdd}
dc Vvb -0.3 1.25 0.001
meas dc vt2 WHEN v(yb)={vdd/2} CROSS=1
set s2 = "$&vt2"
alter Vco dc = {vdd}
dc Vvb -0.3 1.25 0.001
meas dc vt3 WHEN v(yb)={vdd/2} CROSS=1
set s3 = "$&vt3"
echo "vt1=$s1 vt2=$s2 vt3=$s3" > trip.txt
alter Vao dc = 0
alter Vbo dc = 0
alter Vco dc = 0
* ---- transient at the replica-referenced bias points ----
foreach vbv {vb_list}
  alter Vvb dc = $vbv
  tran 10p {tstop}n
{chr(10).join('  ' + x for x in meas)}
  echo "{' '.join(echo)}" >> out.txt
  destroy all
end
.endc
.end
"""


TT_REPLICA = (0.306, 0.571, 0.848)   # from final_trips.csv (tt row)


def sample(args):
    seed, corner, temp, vdd, vbs = args
    _, d = run(deck(seed, corner, temp, vdd, vbs), tag=f"mc_{corner}")
    try:
        tr = parse_kv(d / "trip.txt")[0]
        rows = parse_kv(d / "out.txt")
    except Exception as e:  # keep failures visible
        return dict(seed=seed, error=str(e), dir=str(d))
    out = dict(seed=seed, corner=corner, **tr)
    for name, r in zip(("AND", "MAJ", "OR"), rows):
        out[f"tt_{name}"] = truth(r, vdd)
        out[f"vb_{name}"] = r["vb"]
        out[f"q_{name}"] = r["q"]
    # coupling step measured in the MAJ run: FG(m=7) - FG(m=0) = 3*Delta
    out["delta"] = (rows[1]["fg7"] - rows[1]["fg0"]) / 3.0
    return out


if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    corner = sys.argv[2] if len(sys.argv) > 2 else "tt"
    temp = float(sys.argv[3]) if len(sys.argv) > 3 else 27.0
    vdd = float(sys.argv[4]) if len(sys.argv) > 4 else VDD
    vbs = tuple(float(x) for x in sys.argv[5:8]) if len(sys.argv) > 7 else TT_REPLICA
    with Pool(int(__import__("os").environ.get("NPROC", 8))) as pool:
        res = pool.map(sample, [(1000 + i, corner, temp, vdd, vbs) for i in range(N)])
    df = pd.DataFrame(res)
    df.to_csv(DATA / f"mc_{corner}.csv", index=False)
    tgt = {"AND": "00000001", "MAJ": "00010111", "OR": "01111111"}
    for k, t in tgt.items():
        ok = (df[f"tt_{k}"] == t).mean()
        print(f"{corner} {k}: yield {ok*100:.1f}% ({(df[f'tt_{k}'] == t).sum()}/{len(df)})")
    for c in ("vt1", "vt2", "vt3", "delta"):
        print(f"{c}: mean {df[c].mean():.4f}  sigma {df[c].std()*1e3:.1f} mV")
