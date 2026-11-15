"""
K-input QFG threshold cell: popcount testbench.

Because the nominal cell is symmetric in its inputs, the response depends only
on n = number of asserted inputs.  K+1 instances (n = 0..K) are reset to VB,
released, driven, and sampled.  For each threshold T (1..K) we report the VB
window in which Y = [n >= T] for every n.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ngs import VDD, cell_subckt, header, parse_kv, run

T_RST_END, T_IN, T_SAMPLE, T_STOP = 2.0, 3.0, 7.5, 8.0


def vb_sweep_k(K, params=None, corner="tt", temp=27.0, vdd=VDD, vb_lo=0.0, vb_hi=1.2,
               vb_step=0.01, tag="vbk", cell_text=None) -> pd.DataFrame:
    inst, meas, echo = [], [], ["vb=$&vbv"]
    for n in range(K + 1):
        nodes = []
        for i in range(K):
            nd = f"i{n}_{i}"
            if i < n:
                inst.append(f"V{nd} {nd} 0 PWL(0 0 {T_IN}n 0 {T_IN+0.05}n {vdd})")
            else:
                inst.append(f"V{nd} {nd} 0 0")
            nodes.append(nd)
        name = "QFG_TLG" if K == 3 else f"QFG_TLG{K}"
        inst.append(f"X{n} {' '.join(nodes)} rst vb y{n} yb{n} fg{n} vdd 0 {name}")
        inst.append(f"CL{n} y{n} 0 5f")
        meas += [f"meas tran y{n}v FIND v(y{n}) AT={T_SAMPLE}n",
                 f"meas tran fg{n}v FIND v(fg{n}) AT={T_SAMPLE}n"]
        echo += [f"y{n}=$&y{n}v", f"fg{n}=$&fg{n}v"]
    deck = header(corner, temp) + (cell_text or cell_subckt(params, K=K)) + f"""
Vdd vdd 0 {vdd}
Vrst rst 0 PWL(0 {vdd} {T_RST_END}n {vdd} {T_RST_END+0.05}n 0)
Vvb vb 0 0.5
{chr(10).join(inst)}
.option method=gear reltol=1e-4
.control
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
    _, d = run(deck, tag=f"{tag}{K}")
    df = pd.DataFrame(parse_kv(d / "out.txt"))
    df.attrs["K"] = K
    return df


def threshold_windows(df, K, vdd=VDD):
    hi, lo = 0.8 * vdd, 0.2 * vdd
    vb = df["vb"].to_numpy()
    pats = ["".join("1" if r[f"y{n}"] >= hi else ("0" if r[f"y{n}"] <= lo else "x")
                    for n in range(K + 1)) for _, r in df.iterrows()]
    out = {}
    for T in range(1, K + 1):
        tgt = "".join("1" if n >= T else "0" for n in range(K + 1))
        idx = [i for i, p in enumerate(pats) if p == tgt]
        if not idx:
            out[T] = (np.nan, np.nan, 0.0)
            continue
        best, cur = [idx[0]], [idx[0]]
        for i in idx[1:]:
            cur = cur + [i] if i == cur[-1] + 1 else [i]
            if len(cur) > len(best):
                best = list(cur)
        out[T] = (vb[best[0]], vb[best[-1]], vb[best[-1]] - vb[best[0]])
    return out, pats
