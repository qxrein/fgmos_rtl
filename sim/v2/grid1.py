"""Design-space search for v2 cell sizing (TT, 27C). Writes data/v2/grid1.csv"""
import itertools, sys
from multiprocessing import Pool
import numpy as np, pandas as pd
from tb import vb_sweep, windows
from ngs import DATA

# MIM ~2 fF/um^2: cin 3x3um ~ 20 fF. ballast chosen to give coupling k = Cin/Ctot
def case(args):
    wp, wn, cin_side, k = args
    cin = 2.0*cin_side**2 + 0.4*cin_side      # rough fF estimate (area+perim), only to size ballast
    ctot = cin / k
    cb = max(ctot - 3*cin, 4.0)
    side = (cb/2.0)**0.5
    p = dict(wp=wp, wn=wn, cw=cin_side, cl=cin_side, bw=round(side,2), bl=round(side,2))
    df = vb_sweep(p, vb_lo=-0.0, vb_hi=1.0, vb_step=0.02, tag=f"g1")
    w = windows(df)
    fgmax = df["fg7"].max()
    row = dict(wp=wp, wn=wn, cin_side=cin_side, k=k, ballast_side=round(side,2), fg7_max=fgmax)
    for n,(a,b,c) in w.items():
        row[f"{n}_lo"]=a; row[f"{n}_hi"]=b; row[f"{n}_w"]=c
    row["min_w"]=min(w[n][2] for n in w)
    return row

if __name__ == "__main__":
    grid = list(itertools.product([2,4,8,12],[0.42,0.84],[3.0],[0.15,0.2,0.25]))
    with Pool(10) as pool:
        rows = pool.map(case, grid)
    df = pd.DataFrame(rows).sort_values("min_w", ascending=False)
    df.to_csv(DATA/"grid1.csv", index=False)
    print(df.round(3).to_string())
