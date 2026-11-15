"""
Fan-in scaling, phase 2: timing / energy / area of the best sizing per K (from kscale_windows.csv).

Bench: K+1 instances (popcount n = 0..K), each with its own supply source so that the energy of
each popcount is measured separately. Reset 1 ns, then return-to-zero input pulses of width t_p.
For thresholds T = 1, ceil(K/2), K (OR-K, MAJ-K, AND-K) with V_B at the centre of the window:
  t_pd   : worst input-to-Y delay over the popcounts where Y rises
  E(n)   : supply energy per cycle of the instance with popcount n
  E_avg  : sum_n C(K,n)/2^K E(n)   (uniformly random inputs)
Area: estimated from the measured K=3 layout (155.7 um^2) by adding, per extra input, one input-MIM
tile including the 1.34-um capm halo and one pull-down tile, plus ballast and load growth.
Writes data/v2/kscale_summary.csv, kscale_timing.csv
"""
from __future__ import annotations

from math import ceil, comb
from multiprocessing import Pool

import numpy as np
import pandas as pd

from kscale import CIN_FF, sizing
from ngs import DATA, VDD, cell_subckt, header, parse_kv, run

A3 = 10.4 * 14.97
TILE_CAP = 3.6 * 4.35          # 2.4x2.4 plate + 0.75 via margin + 1.2 halo spacing (um^2)
TILE_NFET = 1.58 * 1.68
MP_AREA_PER_UM = 3.06 * 5.31 / 16.0
T_RST, EDGE = 1.0, 0.05


def area_est(K, p):
    p3, _ = sizing(3, 0.5, 16.0)
    cb3 = 2.0 * p3["bw"] * p3["bl"]; cbk = 2.0 * p["bw"] * p["bl"]
    return A3 + (K - 3) * (TILE_CAP + TILE_NFET) + 1.2 * (cbk - cb3) / 2.0 + MP_AREA_PER_UM * (p["wp"] - 16.0)


def deck(K, p, vb, t_p, cell_text=None):
    name = "QFG_TLG" if K == 3 else f"QFG_TLG{K}"
    ti = T_RST + 2 * EDGE
    tstop = ti + t_p + 1.0
    lines, meas, echo = [], [], []
    for n in range(K + 1):
        nodes = []
        for i in range(K):
            nd = f"i{n}_{i}"
            if i < n:
                lines.append(f"V{nd} {nd} 0 PWL(0 0 {ti}n 0 {ti+EDGE}n {VDD} {ti+EDGE+t_p}n {VDD} {ti+2*EDGE+t_p}n 0)")
            else:
                lines.append(f"V{nd} {nd} 0 0")
            nodes.append(nd)
        lines.append(f"Vdd{n} vdd{n} 0 {VDD}")
        lines.append(f"X{n} {' '.join(nodes)} rst vb y{n} yb{n} fg{n} vdd{n} 0 {name}")
        lines.append(f"CL{n} y{n} 0 5f")
        ts = ti + EDGE + t_p - 0.03
        meas += [f"meas tran y{n}v FIND v(y{n}) AT={ts:.4f}n",
                 f"meas tran q{n} INTEG i(Vdd{n}) FROM=0 TO={tstop:.4f}n",
                 f"meas tran d{n} TRIG v(i{n}_0) VAL={VDD/2} RISE=1 TARG v(y{n}) VAL={VDD/2} RISE=1" if n > 0 else ""]
        echo += [f"y{n}=$&y{n}v", f"q{n}=$&q{n}"] + ([f"d{n}=$&d{n}"] if n > 0 else [])
    return header("tt", 27.0) + (cell_text or cell_subckt(p, K=K)) + f"""
Vrst rst 0 PWL(0 {VDD} {T_RST}n {VDD} {T_RST+EDGE}n 0)
Vvb vb 0 {vb}
{chr(10).join(lines)}
.option method=gear reltol=1e-4
.control
tran 5p {tstop:.4f}n
{chr(10).join(m for m in meas if m)}
echo "{' '.join(echo)}" > out.txt
.endc
.end
"""


def job(args):
    K, p, T, vb, t_p = args
    _, d = run(deck(K, p, vb, t_p), tag=f"kt{K}_{T}")
    r = parse_kv(d / "out.txt")[0]
    yv = [r.get(f"y{n}", np.nan) for n in range(K + 1)]
    truth = "".join("1" if (isinstance(v, float) and v > VDD / 2) else "0" for v in yv)
    want = "".join("1" if n >= T else "0" for n in range(K + 1))
    E = [-VDD * r[f"q{n}"] * 1e15 for n in range(K + 1)]
    Eavg = sum(comb(K, n) / 2 ** K * E[n] for n in range(K + 1))
    dl = [r.get(f"d{n}") for n in range(1, K + 1)]
    dl = [x * 1e12 for x in dl if isinstance(x, float) and x > 0]
    return dict(K=K, T=T, vb=vb, t_p=t_p, truth=truth, ok=truth == want, E_avg_fJ=Eavg, E_max_fJ=max(E),
                tpd_ps=max(dl) if dl else np.nan)


if __name__ == "__main__":
    Wd = pd.read_csv(DATA / "kscale_windows.csv")
    best = (Wd.groupby(["K", "swing", "wp"]).width.min().reset_index()
              .sort_values("width", ascending=False).groupby("K").head(1).set_index("K"))
    jobs, meta = [], {}
    for K, b in best.iterrows():
        p, ctot = sizing(int(K), b.swing, b.wp)
        w = Wd[(Wd.K == K) & (Wd.swing == b.swing) & (Wd.wp == b.wp)].set_index("T")
        meta[K] = dict(p=p, ctot=ctot, min_width=b.width, swing=b.swing, wp=b.wp)
        for T in sorted({1, ceil(K / 2), int(K)}):
            vb = float((w.loc[T, "lo"] + w.loc[T, "hi"]) / 2) if T > 1 else float(w.loc[1, "lo"] + 0.15)
            for t_p in (0.3, 0.5):
                jobs.append((int(K), p, T, round(vb, 4), t_p))
    with Pool(10) as pool:
        res = pd.DataFrame(pool.map(job, jobs))
    res.to_csv(DATA / "kscale_timing.csv", index=False)
    print(res.round(2).to_string())
    rows = []
    for K, m in meta.items():
        r = res[(res.K == K)]
        # choose the shortest pulse that gives correct truth tables for all thresholds
        tp = min((t for t in (0.3, 0.5) if r[r.t_p == t].ok.all()), default=0.5)
        rr = r[r.t_p == tp]
        rows.append(dict(K=K, swing=m["swing"], wp=m["wp"], ctot_ff=m["ctot"], ballast_l=m["p"]["bl"],
                         min_width=m["min_width"], t_p=tp, all_ok=bool(rr.ok.all()), tpd_ps=rr.tpd_ps.max(),
                         E_min=rr.E_avg_fJ.min(), E_max=rr.E_avg_fJ.max(), area_est=area_est(K, m["p"])))
    S = pd.DataFrame(rows)
    S.to_csv(DATA / "kscale_summary.csv", index=False)
    print(S.round(2).to_string())
