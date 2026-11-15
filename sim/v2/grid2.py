"""Corner-aware refinement of v2 sizing. Writes data/v2/grid2.csv"""
import itertools
from multiprocessing import Pool
import numpy as np, pandas as pd
from tb import vb_sweep, windows, classify, TARGETS_Y
from ngs import DATA

CORNERS = [("tt",27,1.80),("ss",100,1.60),("ff",-40,1.95),("sf",27,1.80),("fs",27,1.80)]

def sizing(wp, k, cin_side=3.0):
    cin = 2.0*cin_side**2 + 0.4*cin_side
    cb = max(cin/k - 3*cin, 4.0)
    side = round((cb/2.0)**0.5, 2)
    return dict(wp=wp, wn=0.42, cw=cin_side, cl=cin_side, bw=side, bl=side)

def case(args):
    wp, k, (corner, temp, vdd) = args
    p = sizing(wp, k)
    df = vb_sweep(p, corner=corner, temp=temp, vdd=vdd, vb_lo=0.0, vb_hi=1.0, vb_step=0.02, tag="g2")
    df["corner"]=corner; df["wp"]=wp; df["k"]=k
    df["pat"]=classify(df, vdd)
    return df

if __name__ == "__main__":
    grid = list(itertools.product([12,16,20],[0.10,0.12,0.15],CORNERS))
    with Pool(10) as pool:
        dfs = pool.map(case, grid)
    big = pd.concat(dfs); big.to_csv(DATA/"grid2_raw.csv", index=False)
    rows=[]
    for (wp,k),g in big.groupby(["wp","k"]):
        row=dict(wp=wp,k=k)
        for name,tgt in TARGETS_Y.items():
            # VB values that realise the function at ALL corners
            ok = g.groupby("vb")["pat"].apply(lambda s: all(p==tgt for p in s))
            v = ok[ok].index.to_numpy()
            row[name+"_common"] = f"{v.min():.2f}-{v.max():.2f}" if len(v) else "none"
            row[name+"_w"] = (v.max()-v.min()) if len(v) else 0.0
            for c,_,_ in CORNERS:
                gc=g[g.corner==c]; vv=gc.vb[gc.pat==tgt].to_numpy()
                row[f"{name}_{c}"]=f"{vv.min():.2f}-{vv.max():.2f}" if len(vv) else "none"
        row["min_common_w"]=min(row[n+"_w"] for n in TARGETS_Y)
        rows.append(row)
    s=pd.DataFrame(rows).sort_values("min_common_w",ascending=False)
    s.to_csv(DATA/"grid2.csv",index=False)
    pd.set_option("display.width",250)
    print(s.to_string())
