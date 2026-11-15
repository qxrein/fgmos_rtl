"""Final-design VB sweeps at 5 PVT corners (5 mV step) + DC trip points for replica biasing.
Writes data/v2/final_corners_raw.csv and data/v2/final_trips.csv"""
import sys, itertools
from multiprocessing import Pool
import numpy as np, pandas as pd
from tb import vb_sweep, windows, classify
from ngs import DATA, VDD, cell_subckt, header, parse_kv, run

P = dict(wp=16, wn=0.42, cw=2.0, cl=2.0, bw=4.85, bl=4.85)
CORNERS = [("tt",27,1.80),("ss",100,1.60),("ff",-40,1.95),("sf",27,1.80),("fs",27,1.80)]

def trips(corner, temp, vdd, P=P):
    """DC: FG forced; for n pull-downs ON find V_FG where YB = VDD/2."""
    out = {}
    for n in (1,2,3):
        ins = " ".join("vdd" if i<n else "0" for i in range(3))
        deck = header(corner,temp)+cell_subckt(P)+f"""
Vdd vdd 0 {vdd}
Vrst rst 0 0
Vvb vb 0 0
Vfg fgx 0 0.5
Rfg fgx fg 1
X1 {ins} rst vb y yb fg vdd 0 QFG_TLG
.control
dc Vfg -0.3 1.8 0.0005
meas dc vt WHEN v(yb)={vdd/2} CROSS=1
echo "vt=$&vt" > out.txt
.endc
.end
"""
        _, d = run(deck, tag=f"trip_{corner}")
        out[n] = parse_kv(d/"out.txt")[0]["vt"]
    return out

def job(c):
    corner,temp,vdd = c
    df = vb_sweep(P, corner=corner, temp=temp, vdd=vdd, vb_lo=-0.1, vb_hi=1.2, vb_step=0.005, tag="fin")
    df["corner"]=corner
    # coupling step from FG(n)-FG(0) at mid VB
    r = df.iloc[(df.vb-0.5).abs().argmin()]
    dfg = np.mean([r["fg7"]-r["fg3"], r["fg3"]-r["fg1"], r["fg1"]-r["fg0"]])  # 0->1->2->3 inputs
    t = trips(corner,temp,vdd)
    return df, dict(corner=corner,temp=temp,vdd=vdd,delta=dfg,vt1=t[1],vt2=t[2],vt3=t[3])

if __name__=="__main__":
    with Pool(5) as pool:
        res = pool.map(job, CORNERS)
    raw = pd.concat([r[0] for r in res]); raw.to_csv(DATA/"final_corners_raw.csv", index=False)
    tr = pd.DataFrame([r[1] for r in res])
    rows=[]
    for (df,_),t in zip(res, tr.to_dict("records")):
        w = windows(df, t["vdd"])
        d = t["delta"]
        u = {n: t[f"vt{n}"] - n*d for n in (1,2,3)}
        t.update({f"u{n}":u[n] for n in u})
        # replica-referenced bias targets
        t["vb_AND"] = 0.5*(u[3]+u[2]); t["vb_MAJ"] = 0.5*(u[2]+u[1]); t["vb_OR"] = u[1] + 0.5*(u[1]-u[2])
        for name in ("OR3","MAJ3","AND3"):
            t[f"{name}_lo"], t[f"{name}_hi"], t[f"{name}_w"] = w[name]
        rows.append(t)
    out = pd.DataFrame(rows); out.to_csv(DATA/"final_trips.csv", index=False)
    pd.set_option("display.width",250)
    print(out.round(3).to_string())
