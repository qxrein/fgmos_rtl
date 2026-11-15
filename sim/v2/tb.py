"""
Testbenches for the v2 QFG threshold-logic cell.

`vb_sweep` instantiates eight copies of the cell (one per input minterm),
resets every floating gate to VB with all inputs low, releases the reset,
applies the minterm, and samples YB / Y / FG late in the evaluation phase.
"""
from __future__ import annotations

import itertools

import numpy as np
import pandas as pd

from ngs import VDD, cell_subckt, header, parse_kv, run

MINTERMS = list(itertools.product([0, 1], repeat=3))  # (A,B,C)

# timing (ns)
T_RST_END = 2.0
T_IN = 3.0
T_SAMPLE = 7.5
T_STOP = 8.0


def _instances(load_ff: float = 5.0, vdd: float = VDD) -> str:
    s = []
    for m, (a, b, c) in enumerate(MINTERMS):
        for name, bit in zip("abc", (a, b, c)):
            if bit:
                s.append(f"V{name}{m} {name}{m} 0 PWL(0 0 {T_IN}n 0 {T_IN+0.05}n {vdd})")
            else:
                s.append(f"V{name}{m} {name}{m} 0 0")
        s.append(f"X{m} a{m} b{m} c{m} rst vb y{m} yb{m} fg{m} vdd 0 QFG_TLG")
        s.append(f"CL{m} y{m} 0 {load_ff}f")
    return "\n".join(s)


def vb_sweep(params=None, corner="tt", temp=27.0, vdd=VDD, vb_lo=0.0, vb_hi=1.2,
             vb_step=0.01, mc=False, seed=None, tag="vbsweep", cell_text=None) -> pd.DataFrame:
    meas = []
    echo = ["vb=$&vbv"]
    for m in range(8):
        meas += [
            f"meas tran yb{m}v FIND v(yb{m}) AT={T_SAMPLE}n",
            f"meas tran y{m}v FIND v(y{m}) AT={T_SAMPLE}n",
            f"meas tran fg{m}v FIND v(fg{m}) AT={T_SAMPLE}n",
        ]
        echo += [f"yb{m}=$&yb{m}v", f"y{m}=$&y{m}v", f"fg{m}=$&fg{m}v"]
    seed_line = f"set rndseed={seed}" if seed is not None else ""
    deck = header(corner, temp, mc) + (cell_text or cell_subckt(params)) + f"""
Vdd vdd 0 {vdd}
Vrst rst 0 PWL(0 {vdd} {T_RST_END}n {vdd} {T_RST_END+0.05}n 0)
Vvb vb 0 0.5
{_instances(vdd=vdd)}
.option method=gear reltol=1e-4
.control
{seed_line}
let vbv = {vb_lo}
while vbv le {vb_hi + 1e-9}
  alter Vvb dc = vbv
  tran 10p {T_STOP}n
  {chr(10).join('  ' + x for x in meas)}
  echo "{' '.join(echo)}" >> out.txt
  destroy all
  let vbv = vbv + {vb_step}
end
.endc
.end
"""
    _, d = run(deck, tag=tag)
    rows = parse_kv(d / "out.txt")
    return pd.DataFrame(rows)


def classify(df: pd.DataFrame, vdd=VDD, node="y"):
    """Return per-VB 8-bit truth vector of the restored output Y (or YB)."""
    hi, lo = 0.8 * vdd, 0.2 * vdd
    pats = []
    for _, r in df.iterrows():
        bits = []
        for m in range(8):
            v = r[f"{node}{m}"]
            bits.append("1" if v >= hi else ("0" if v <= lo else "x"))
        pats.append("".join(bits))
    return pats


TARGETS_Y = {
    "OR3": "".join(str(int(a or b or c)) for a, b, c in MINTERMS),
    "MAJ3": "".join(str(int(a + b + c >= 2)) for a, b, c in MINTERMS),
    "AND3": "".join(str(int(a and b and c)) for a, b, c in MINTERMS),
}


def windows(df: pd.DataFrame, vdd=VDD):
    """Contiguous VB windows (min,max,width) where Y equals each target."""
    pats = classify(df, vdd)
    vb = df["vb"].to_numpy()
    out = {}
    for name, tgt in TARGETS_Y.items():
        idx = [i for i, p in enumerate(pats) if p == tgt]
        if not idx:
            out[name] = (np.nan, np.nan, 0.0)
            continue
        # longest contiguous run
        best, cur = [idx[0]], [idx[0]]
        for i in idx[1:]:
            if i == cur[-1] + 1:
                cur.append(i)
            else:
                cur = [i]
            if len(cur) > len(best):
                best = list(cur)
        out[name] = (vb[best[0]], vb[best[-1]], vb[best[-1]] - vb[best[0]])
    return out
