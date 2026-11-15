"""
Fan-in scaling of the QFG threshold cell (K = 3, 5, 7, 9).

Sizing rule (kept deliberately simple and stated in the paper):
  * input MIMs stay at the 2 x 2 um minimum (~9.5 fF);
  * the ballast MIM is sized so that the total FG swing K*Delta equals S (S = 0.5 V for K=3);
  * the PMOS load width scales so that it can still out-drive (K-1) pull-downs at the AND-K bias.
For each K we find the VB window of every threshold T = 1..K (popcount bench, TT, 27 C)
and run timing/energy for the AND-K (worst static current) and MAJ-K settings.
Writes data/v2/kscale_windows.csv
"""
from __future__ import annotations

import sys
from multiprocessing import Pool

import numpy as np
import pandas as pd

from ngs import DATA
from tbk import threshold_windows, vb_sweep_k

CIN_FF = 9.52          # 2x2 um MIM (carea 2 fF/um^2, cperi 0.19 fF/um)
CG_FF_PER_UM = 23.0 / 16.0   # PMOS gate + overlap cap per um of width (from the K=3 design)


def sizing(K, swing=0.5, wp=None):
    wp = wp if wp is not None else 16.0 * (K - 1) / 2.0
    k = swing / (1.8 * K)
    ctot = CIN_FF / k
    cbl = max(ctot - K * CIN_FF - CG_FF_PER_UM * wp, 10.0)
    # ballast as a 9.2 um-wide MIM (like the layout), length from area: C = 2*A + 0.19*P
    w = 9.2
    l = max((cbl - 0.38 * w) / (2 * w + 0.38), 2.0)
    return dict(wp=wp, bw=w, bl=round(l, 2)), ctot


def job(args):
    K, swing, wp = args
    p, ctot = sizing(K, swing, wp)
    df = vb_sweep_k(K, p, vb_lo=-0.05, vb_hi=1.25, vb_step=0.01, tag=f"ks_{swing}_{wp}_")
    w, _ = threshold_windows(df, K)
    delta = float(np.median([(r[f"fg{K}"] - r["fg0"]) / K for _, r in df.iterrows()]))
    rows = []
    for T, (lo, hi, wd) in w.items():
        rows.append(dict(K=K, swing=swing, wp=p["wp"], ballast_l=p["bl"], ctot_ff=ctot, delta=delta,
                         T=T, lo=lo, hi=hi, width=wd))
    return rows


if __name__ == "__main__":
    grid = []
    for K in (3, 5, 7, 9):
        for swing in (0.5, 0.7):
            for f in (1.0,):
                grid.append((K, swing, round(16.0 * (K - 1) / 2.0 * f, 1)))
    with Pool(int(__import__("os").environ.get("NPROC", 10))) as p:
        res = p.map(job, grid)
    df = pd.DataFrame([r for rr in res for r in rr])
    df.to_csv(DATA / "kscale_windows.csv", index=False)
    s = df.groupby(["K", "swing", "wp"]).agg(min_width=("width", "min"), n_ok=("width", lambda x: (x > 0).sum()),
                                             delta=("delta", "first"), ctot=("ctot_ff", "first"))
    print(s.round(3).to_string())
