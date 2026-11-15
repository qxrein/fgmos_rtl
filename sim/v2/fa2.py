"""Full adder, pass 2: timing/energy at the window centres, and the SS window vs pulse width."""
from multiprocessing import Pool
import numpy as np, pandas as pd
import fa
from ngs import DATA, run, parse_kv

def ss_sweep(tp):
    fa.T_P = tp
    vbs = np.round(np.arange(0.50, 0.90 + 1e-9, 0.01), 4)
    _, d = run(fa.deck("ss", fa.VB1["ss"], vbs, t_p=tp), tag="fa_ss_tp")
    rows = []
    for r in parse_kv(d / "out.txt"):
        c, s = fa.truths(r, 1.6)
        rows.append(dict(t_p=tp, vb2=r["vb2"], ok=(c == fa.COUT and s == fa.SUM)))
    return rows

if __name__ == "__main__":
    W = pd.read_csv(DATA / "fa_window.csv")
    cen = {c: round(float((g[g.ok].vb2.min() + g[g.ok].vb2.max()) / 2), 4) for c, g in W.groupby("corner")}
    with Pool(8) as p:
        T = p.map_async(fa.timing_at, list(cen.items()))
        S = p.map_async(ss_sweep, [0.6, 1.0, 1.5])
        T = pd.DataFrame(T.get()); S = pd.DataFrame([r for rr in S.get() for r in rr])
    T.to_csv(DATA / "fa_timing.csv", index=False); S.to_csv(DATA / "fa_ss_tp.csv", index=False)
    print(T.round(2).to_string())
    for tp, g in S.groupby("t_p"):
        v = g[g.ok].vb2
        print("SS t_p", tp, "window", (v.min(), v.max()) if len(v) else None)
