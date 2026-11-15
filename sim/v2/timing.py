"""
Transient timing / energy of the v2 cell (schematic and Magic-extracted).

Uses the sequential reset->evaluate bench (tbseq) with waveform dump.
Per cycle k (minterm k):
  t_pd   : input edge (50 %) -> Y crossing VDD/2 (only cycles where Y rises)
  t_rst  : RST rising (50 %) -> Y falling below VDD/2 (precharge/reset delay)
  E_cyc  : VDD * integral(I_VDD) over the cycle
  I_stat : supply current at the end of evaluation (ratioed static current)
Usage: python timing.py [schematic|pex] [corner temp vdd vb_and vb_maj vb_or]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from ngs import DATA, VDD, pex_cell_text
from tbseq import T_E, T_R, seq_run
from tbseq import T_EDGE

MODES = ("AND3", "MAJ3", "OR3")


def analyse(wave_file: Path, vdd: float, t_p=None):
    a = np.loadtxt(wave_file, skiprows=1)
    t = a[:, 0]
    rst, va, vb, vc, fg, yb, y, idd = (a[:, i] for i in range(1, 9))
    tc = (T_R + T_E) * 1e-9
    rows = []
    for k in range(8):
        t0 = k * tc
        t_in = t0 + (T_R + 2 * T_EDGE + T_EDGE / 2) * 1e-9
        t_end = t0 + tc
        t_eval_end = t0 + (T_R + T_E - 0.2) * 1e-9 if t_p is None else t_in + (T_EDGE / 2 + t_p - 0.03) * 1e-9
        m = (t >= t0) & (t < t_end)
        e = vdd * np.trapezoid(-idd[m], t[m])
        # static current at end of evaluation
        ie = -np.interp(t_eval_end, t, idd)
        # propagation delay (Y rising after inputs), searched within the evaluation window
        mm = (t >= t_in) & (t <= t_eval_end)
        tpd = np.nan
        if y[mm][-1] > vdd / 2 and y[mm][0] < vdd / 2:
            idx = np.argmax(y[mm] > vdd / 2)
            tt, yy = t[mm], y[mm]
            tpd = np.interp(vdd / 2, [yy[idx - 1], yy[idx]], [tt[idx - 1], tt[idx]]) - t_in
        # reset delay: Y falls after the inputs return low (RZ) / RST rises
        trst = np.nan
        t_r = t_end - T_EDGE * 1e-9 / 2 if t_p is None else t_eval_end + 0.03e-9 + T_EDGE * 1e-9 / 2
        mr = (t >= t_r) & (t < t_r + T_R * 1e-9)
        if mr.any() and y[mr][0] > vdd / 2 and y[mr][-1] < vdd / 2:
            idx = np.argmax(y[mr] < vdd / 2)
            tt, yy = t[mr], y[mr]
            trst = np.interp(vdd / 2, [yy[idx], yy[idx - 1]], [tt[idx], tt[idx - 1]]) - t_r
        rows.append(dict(minterm=k, E_fJ=e * 1e15, I_static_uA=ie * 1e6, tpd_ps=tpd * 1e12, trst_ps=trst * 1e12))
    return pd.DataFrame(rows)


def run(view="schematic", corner="tt", temp=27.0, vdd=VDD, vbs=(0.306, 0.571, 0.848), t_p=None):
    ct = pex_cell_text() if view == "pex" else None
    df = seq_run(vbs=vbs, corner=corner, temp=temp, vdd=vdd, tag=f"tim_{view}_{corner}",
                 cell_text=ct, save_wave=True, t_p=t_p)
    d = Path(df.attrs["dir"])
    out = []
    for mode, vbv in zip(MODES, vbs):
        f = sorted(d.glob("wave_*.txt"), key=lambda p: abs(float(p.stem.split("_")[1]) - vbv))[0]
        r = analyse(f, vdd, t_p)
        r["mode"], r["view"], r["corner"], r["vb"], r["t_p_ns"] = mode, view, corner, vbv, t_p
        r["truth"] = "".join(str(int(v > vdd / 2)) for v in [df.iloc[list(vbs).index(vbv)][f"y{k}"] for k in range(8)])
        out.append(r)
    return pd.concat(out)


if __name__ == "__main__":
    view = sys.argv[1] if len(sys.argv) > 1 else "schematic"
    corner = sys.argv[2] if len(sys.argv) > 2 else "tt"
    temp = float(sys.argv[3]) if len(sys.argv) > 3 else 27.0
    vdd = float(sys.argv[4]) if len(sys.argv) > 4 else VDD
    vbs = tuple(float(x) for x in sys.argv[5:8]) if len(sys.argv) > 7 else (0.306, 0.571, 0.848)
    t_p = float(sys.argv[8]) if len(sys.argv) > 8 else None
    df = run(view, corner, temp, vdd, vbs, t_p)
    f = DATA / f"timing_{view}_{corner}_tp{t_p}.csv"
    df.to_csv(f, index=False)
    s = df.groupby("mode").agg(E_fJ=("E_fJ", "mean"), tpd_ps=("tpd_ps", "max"),
                                tpd_mean=("tpd_ps", "mean"), trst_ps=("trst_ps", "max"),
                                Istat_max_uA=("I_static_uA", "max"))
    print(f"[{view} {corner} t_p={t_p}]\n{s.round(2).to_string()}")
    print(df.groupby("mode")["truth"].first().to_string())
