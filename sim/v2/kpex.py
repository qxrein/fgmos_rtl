"""
Post-layout (Magic-extracted) simulation of the K=5 and K=9 cells (TT, 27 C):
windows of every threshold T (popcount bench) and timing/energy at the window centres
(T = 1, ceil(K/2), K) with 0.3-ns RZ pulses, schematic vs extracted.
Writes data/v2/kpex_windows.csv, kpex_timing.csv
"""
from math import ceil
from multiprocessing import Pool
import numpy as np, pandas as pd
from kscale import sizing
from kscale2 import job as tjob, deck
from ngs import DATA, pex_cell_text_k, run, parse_kv
from tbk import threshold_windows, vb_sweep_k
import kscale2

def win(args):
    K, view = args
    p, _ = sizing(K, 0.7, 8.0 * (K - 1))
    ct = pex_cell_text_k(K) if view == "pex" else None
    df = vb_sweep_k(K, p, vb_lo=-0.05, vb_hi=1.25, vb_step=0.01, tag=f"kp{view}", cell_text=ct)
    w, _ = threshold_windows(df, K)
    return [dict(K=K, view=view, T=T, lo=lo, hi=hi, width=wd) for T, (lo, hi, wd) in w.items()]

def tim(args):
    K, view, T, vb = args
    p, _ = sizing(K, 0.7, 8.0 * (K - 1))
    ct = pex_cell_text_k(K) if view == "pex" else None
    _, d = run(deck(K, p, vb, 0.3, ct), tag=f"kpt{K}{view}")
    r = parse_kv(d / "out.txt")[0]
    from math import comb
    VDD = 1.8
    y = "".join("1" if isinstance(r.get(f"y{n}"), float) and r[f"y{n}"] > VDD / 2 else "0" for n in range(K + 1))
    want = "".join("1" if n >= T else "0" for n in range(K + 1))
    E = [-VDD * r[f"q{n}"] * 1e15 for n in range(K + 1)]
    dl = [r.get(f"d{n}") for n in range(1, K + 1)]
    dl = [x * 1e12 for x in dl if isinstance(x, float) and x > 0]
    return dict(K=K, view=view, T=T, vb=vb, truth=y, ok=y == want, tpd_ps=max(dl) if dl else np.nan,
                E_avg_fJ=sum(comb(K, n) / 2 ** K * E[n] for n in range(K + 1)))

if __name__ == "__main__":
    with Pool(4) as p:
        W = pd.DataFrame([r for rr in p.map(win, [(K, v) for K in (5, 9) for v in ("schematic", "pex")]) for r in rr])
    W.to_csv(DATA / "kpex_windows.csv", index=False)
    print(W.round(3).to_string())
    jobs = []
    for (K, view), g in W.groupby(["K", "view"]):
        g = g.set_index("T")
        for T in sorted({1, ceil(K / 2), K}):
            vb = float(g.loc[T, "lo"] + 0.15) if T == 1 else float((g.loc[T, "lo"] + g.loc[T, "hi"]) / 2)
            jobs.append((K, view, T, round(vb, 4)))
    with Pool(6) as p:
        Tm = pd.DataFrame(p.map(tim, jobs))
    Tm.to_csv(DATA / "kpex_timing.csv", index=False)
    print(Tm.round(2).to_string())
