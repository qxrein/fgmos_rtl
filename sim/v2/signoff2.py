"""
Sign-off pass 2: replica-referenced VB using the *measured* per-corner coupling step Delta
(a capacitive replica of the FG network tracks Delta), followed by timing with long RZ pulses
(to obtain the full worst-case t_pd) and then at t_p = max(0.3 ns, 1.5 x worst t_pd).
Outputs: data/v2/signoff2_vb.csv, signoff2_timing.csv
"""
from multiprocessing import Pool
import numpy as np, pandas as pd
from ngs import DATA
import timing

T = pd.read_csv(DATA/"signoff_trips_raw.csv")
W = pd.read_csv(DATA/"signoff_windows.csv")
d = W[W.view=="schematic"].set_index("corner")["delta"]
T["delta"] = T.corner.map(d)
for n in (1,2,3): T[f"u{n}"] = T[f"vt{n}"] - n*T.delta
T["vb_AND"]=(T.u3+T.u2)/2; T["vb_MAJ"]=(T.u2+T.u1)/2; T["vb_OR"]=T.u1+(T.u1-T.u2)/2
for view in ("schematic","pex"):
    w = W[W.view==view].set_index("corner")
    for m,c in (("AND","AND3"),("MAJ","MAJ3"),("OR","OR3")):
        T[f"margin_{m}_{view}"] = [min(r[f"vb_{m}"]-w.loc[r.corner,f"{c}_lo"], (w.loc[r.corner,f"{c}_hi"]-r[f"vb_{m}"]) if c!="OR3" else 9) for _,r in T.iterrows()]
T.to_csv(DATA/"signoff2_vb.csv", index=False)
print(T.round(3).to_string())

def job(a):
    view,(c,t,v,vbs),tp = a
    r = timing.run(view,c,t,v,vbs,tp); return r

if __name__=="__main__":
    rows=[(r.corner,r.temp,r.vdd,(round(r.vb_AND,4),round(r.vb_MAJ,4),round(r.vb_OR,4))) for r in T.itertuples()]
    with Pool(5) as p:
        long = pd.concat(p.map(job,[(v,x,1.5) for x in rows for v in ("schematic","pex")]))
    worst = long.groupby(["corner"]).tpd_ps.max()
    print("worst tpd (ps) per corner (1.5-ns pulses):"); print(worst)
    tp = {c: round(max(0.3, 1.5*worst[c]/1000), 2) for c in worst.index}
    with Pool(5) as p:
        short = pd.concat(p.map(job,[(v,x,tp[x[0]]) for x in rows for v in ("schematic","pex")]))
    out = pd.concat([long.assign(run="long_1p5ns"), short.assign(run="sized")])
    out.to_csv(DATA/"signoff2_timing.csv", index=False)
    s = out.groupby(["run","corner","view","mode"]).agg(tp=("t_p_ns","first"),truth=("truth","first"),E_fJ=("E_fJ","mean"),
          tpd_max=("tpd_ps","max"),trst_max=("trst_ps","max"),Istat=("I_static_uA","max"))
    pd.set_option("display.width",200); print(s.round(1).to_string())
