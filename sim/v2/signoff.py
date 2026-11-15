"""
PVT sign-off of the final v2 cell, schematic vs Magic-extracted (PEX).
Per corner: replica trip points (DC) -> replica-referenced VB per mode -> VB windows (transient,
8 minterms) and timing/energy at the replica VBs with RZ inputs (t_p = 0.3 ns).
Outputs: data/v2/signoff_trips.csv, signoff_windows.csv, signoff_timing.csv
"""
from multiprocessing import Pool
import numpy as np, pandas as pd
from ngs import DATA, VDD, cell_subckt, header, parse_kv, run, pex_cell_text
from tb import vb_sweep, windows
import timing

CORNERS = [("tt",27,1.80),("ss",100,1.60),("ff",-40,1.95),("sf",27,1.80),("fs",27,1.80)]
TP = 0.3

def trips(corner, temp, vdd, cell_text=None):
    out = {}
    for n in (1,2,3):
        ins = " ".join("vdd" if i<n else "0" for i in range(3))
        deck = header(corner,temp)+(cell_text or cell_subckt())+f"""
Vdd vdd 0 {vdd}
Vrst rst 0 {vdd}
Vvb vb 0 0.5
X1 {ins} rst vb y yb fg vdd 0 QFG_TLG
.control
dc Vvb -0.3 1.25 0.0005
meas dc vt WHEN v(yb)={vdd/2} CROSS=1
echo "vt=$&vt" > out.txt
.endc
.end
"""
        _, d = run(deck, tag=f"strip_{corner}")
        out[n] = parse_kv(d/"out.txt")[0]["vt"]
    return out

def task(args):
    kind, view, (corner,temp,vdd), vbs = args
    ct = pex_cell_text() if view=="pex" else None
    if kind=="win":
        df = vb_sweep(corner=corner,temp=temp,vdd=vdd,vb_lo=-0.05,vb_hi=1.25,vb_step=0.01,tag=f"sw_{view}",cell_text=ct)
        w = windows(df, vdd)
        r = dict(view=view,corner=corner)
        for k,(lo,hi,wd) in w.items(): r.update({f"{k}_lo":lo,f"{k}_hi":hi,f"{k}_w":wd})
        r["delta"] = float(np.mean([(row.fg7-row.fg0)/3 for _,row in df.iterrows() if 0.2<row.vb<0.8]))
        return ("win", r)
    else:
        t = timing.run(view, corner, temp, vdd, vbs, TP)
        return ("tim", t)

if __name__=="__main__":
    # 1) replica VBs per corner from schematic DC trip points (what an on-chip replica would see)
    with Pool(10) as p:
        tr = p.starmap(trips, [(c,t,v) for c,t,v in CORNERS])
    # coupling step per input from the earlier final-design sweep (nominal 0.167 V); use measured per corner later
    rows=[]
    for (c,t,v),x in zip(CORNERS,tr):
        rows.append(dict(corner=c,temp=t,vdd=v,vt1=x[1],vt2=x[2],vt3=x[3]))
    T = pd.DataFrame(rows)
    T.to_csv(DATA/"signoff_trips_raw.csv",index=False)
    # Delta per corner (capacitive ratio x VDD): measured in earlier run, scales with VDD
    d0 = 0.167/1.8
    T["delta"] = d0*T.vdd
    for n in (1,2,3): T[f"u{n}"] = T[f"vt{n}"] - n*T.delta
    T["vb_AND"]=(T.u3+T.u2)/2; T["vb_MAJ"]=(T.u2+T.u1)/2; T["vb_OR"]=T.u1+(T.u1-T.u2)/2
    T.to_csv(DATA/"signoff_trips.csv",index=False)
    print(T.round(3).to_string())
    jobs=[]
    for (c,t,v),r in zip(CORNERS,T.to_dict("records")):
        vbs=(round(r["vb_AND"],4),round(r["vb_MAJ"],4),round(r["vb_OR"],4))
        for view in ("schematic","pex"):
            jobs.append(("win",view,(c,t,v),vbs))
            jobs.append(("tim",view,(c,t,v),vbs))
    with Pool(10) as p:
        res = p.map(task, jobs)
    W = pd.DataFrame([r for k,r in res if k=="win"]); W.to_csv(DATA/"signoff_windows.csv",index=False)
    Tm = pd.concat([r for k,r in res if k=="tim"]); Tm.to_csv(DATA/"signoff_timing.csv",index=False)
    pd.set_option("display.width",250)
    print(W.round(3).to_string())
    s = Tm.groupby(["corner","view","mode"]).agg(truth=("truth","first"),E_fJ=("E_fJ","mean"),tpd_max_ps=("tpd_ps","max"),Istat_max_uA=("I_static_uA","max"))
    print(s.round(1).to_string())
