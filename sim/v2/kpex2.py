"""K=9 timing at t_p = 0.6 ns (1.5 x the worst extracted delay at 0.3 ns), schematic and extracted."""
from multiprocessing import Pool
import pandas as pd
import kpex
from ngs import DATA
from kscale import sizing
from kscale2 import deck
from ngs import run, parse_kv, pex_cell_text_k
import numpy as np
from math import comb

def tim(args):
    K, view, T, vb, tp = args
    p, _ = sizing(K, 0.7, 8.0 * (K - 1))
    ct = pex_cell_text_k(K) if view == "pex" else None
    _, d = run(deck(K, p, vb, tp, ct), tag=f"kpt2{K}{view}")
    r = parse_kv(d / "out.txt")[0]
    y = "".join("1" if isinstance(r.get(f"y{n}"), float) and r[f"y{n}"] > 0.9 else "0" for n in range(K + 1))
    want = "".join("1" if n >= T else "0" for n in range(K + 1))
    E = [-1.8 * r[f"q{n}"] * 1e15 for n in range(K + 1)]
    dl = [x * 1e12 for x in (r.get(f"d{n}") for n in range(1, K + 1)) if isinstance(x, float) and x > 0]
    return dict(K=K, view=view, T=T, vb=vb, t_p=tp, truth=y, ok=y == want, tpd_ps=max(dl) if dl else np.nan,
                E_avg_fJ=sum(comb(K, n) / 2 ** K * E[n] for n in range(K + 1)))

if __name__ == "__main__":
    old = pd.read_csv(DATA / "kpex_timing.csv")
    jobs = [(9, r.view, r.T, r.vb, 0.6) for r in old[old.K == 9].itertuples()]
    with Pool(6) as p:
        new = pd.DataFrame(p.map(tim, jobs))
    old["t_p"] = 0.3
    out = pd.concat([old[old.K != 9], new])
    out.to_csv(DATA / "kpex_timing.csv", index=False)
    print(out.round(2).to_string())
