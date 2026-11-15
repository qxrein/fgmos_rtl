"""
Robustness of the extracted (PEX) cell at the TT process corner.

Sweeps (one parameter at a time, the others nominal: TT, 27 C, 1.80 V, 50-ps input edges, 5-fF load,
1-ns reset, RZ pulse 0.3 ns):
  * supply 1.62 ... 1.98 V and temperature -40 ... 125 C  -- the replica-referenced V_B is
    recomputed for each condition from DC trip points and the measured coupling step (a replica
    tracks supply and temperature);
  * input edge time 20 ... 200 ps;
  * output load 5 ... 50 fF;
  * reset-phase width 1.0 ... 0.1 ns (minimum reset that still writes FG correctly).
Per condition: truth tables of AND3/MAJ3/OR3, worst t_pd, mean energy per operation.
Writes data/v2/robust.csv
"""
from __future__ import annotations

from multiprocessing import Pool

import numpy as np
import pandas as pd

import tbseq
import timing
from ngs import DATA, header, parse_kv, pex_cell_text, run

TGT = {"AND3": "00000001", "MAJ3": "00010111", "OR3": "01111111"}


def replica_vbs(temp, vdd):
    vt = {}
    for n in (1, 2, 3):
        ins = " ".join("vdd" if i < n else "0" for i in range(3))
        deck = header("tt", temp) + pex_cell_text() + f"""
Vdd vdd 0 {vdd}
Vrst rst 0 {vdd}
Vvb vb 0 0.5
X1 {ins} rst vb y yb fg vdd 0 QFG_TLG
.control
dc Vvb -0.3 1.3 0.001
meas dc vt WHEN v(yb)={vdd/2} CROSS=1
echo "vt=$&vt" > out.txt
.endc
.end
"""
        _, d = run(deck, tag="rob_trip")
        vt[n] = parse_kv(d / "out.txt")[0]["vt"]
    # coupling step from a short transient at mid bias
    df = tbseq.seq_run(vbs=(0.55,), temp=temp, vdd=vdd, cell_text=pex_cell_text(), tag="rob_delta")
    delta = float((df.iloc[0].fg7 - df.iloc[0].fg0) / 3)
    u = {n: vt[n] - n * delta for n in vt}
    return (round((u[3] + u[2]) / 2, 4), round((u[2] + u[1]) / 2, 4), round(u[1] + (u[1] - u[2]) / 2, 4)), delta


def job(args):
    try:
        return _job(args)
    except Exception as e:  # keep the sweep going; report the failing condition
        return [dict(kind=args[0], value=args[1], mode="ALL", ok=False, error=repr(e)[:200])]


def _job(args):
    kind, val = args
    temp, vdd = 27.0, 1.8
    if kind == "vdd":
        vdd = val
    if kind == "temp":
        temp = val
    if kind in ("vdd", "temp"):
        vbs, delta = replica_vbs(temp, vdd)
    else:
        vbs, delta = (0.307, 0.571, 0.849), 0.167
    # module-level timing knobs (each worker process has its own copy)
    tbseq.T_EDGE = val * 1e-3 if kind == "edge" else 0.05
    tbseq.T_R = val if kind == "reset" else 1.0
    timing.T_EDGE = tbseq.T_EDGE; timing.T_R = tbseq.T_R
    cload = val if kind == "load" else 5.0
    tp = 0.3 if kind != "load" else min(1.5, max(0.3, 0.3 * val / 5.0))
    ct = pex_cell_text()
    df = tbseq.seq_run(vbs=vbs, temp=temp, vdd=vdd, tag=f"rob_{kind}", cell_text=ct, save_wave=True,
                       t_p=tp, cload_ff=cload)
    from pathlib import Path
    d = Path(df.attrs["dir"])
    rows = []
    for mode, vb in zip(("AND3", "MAJ3", "OR3"), vbs):
        f = sorted(d.glob("wave_*.txt"), key=lambda p: abs(float(p.stem.split("_")[1]) - vb))[0]
        r = timing.analyse(f, vdd, tp)
        row = df.iloc[list(vbs).index(vb)]
        truth = "".join(("1" if row[f"y{k}"] > vdd / 2 else "0") if isinstance(row.get(f"y{k}"), float) else "x"
                        for k in range(8))
        rows.append(dict(kind=kind, value=val, temp=temp, vdd=vdd, mode=mode, vb=vb, delta=delta, t_p=tp,
                         truth=truth, ok=truth == TGT[mode], tpd_ps=r.tpd_ps.max(), E_fJ=r.E_fJ.mean()))
    return rows


if __name__ == "__main__":
    jobs = ([("vdd", v) for v in (1.62, 1.71, 1.80, 1.89, 1.98)] +
            [("temp", t) for t in (-40.0, 0.0, 27.0, 85.0, 125.0)] +
            [("edge", e) for e in (20.0, 100.0, 200.0)] +
            [("load", c) for c in (5.0, 20.0, 50.0)] +
            [("reset", r) for r in (0.5, 0.3, 0.2, 0.1)])
    with Pool(10) as p:
        res = p.map(job, jobs)
    df = pd.DataFrame([r for rr in res for r in rr])
    df.to_csv(DATA / "robust.csv", index=False)
    pd.set_option("display.width", 200)
    print(df.round(3).to_string())
