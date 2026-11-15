"""
Replica-cell self-calibration of V_B, evaluated with Monte Carlo at all five PVT corners.

Implementation being modelled: one extra copy of the cell (the replica) is exercised with the
test patterns n = T-1 and n = T while a DAC sweeps V_B (binary search). The search finds the
replica's window edges, and the DAC is set to the window centre. All working cells then share
that V_B through a buffer.

Per corner (N mismatch samples, schematic, local mismatch on all devices):
  * mc.sample() gives the DC trip voltages V_t,n, the coupling step Delta and the transient
    truth tables at the nominal calibrated V_B;
  * the transient window of sample i for threshold T is modelled as
        [u_T,i + c_lo,T ,  u_{T-1},i + c_hi,T],   u_n,i = V_t,n,i - n*Delta_i,
    where c_lo/c_hi are the systematic transient-vs-DC offsets measured at that corner without
    mismatch (data/v2/signoff_windows.csv, signoff_trips_raw.csv);
  * the model is validated against the transient truth tables (agreement rate);
  * calibration: V_B = centre of the replica's window, quantised to a b-bit DAC over 0-1.25 V,
    plus a Gaussian buffer offset. Yield = fraction of (replica, victim) pairs, i != j, for which
    every mode lies inside the victim's window.
Writes data/v2/calib_samples.csv, calib_yield.csv
"""
from __future__ import annotations

import itertools
import sys
from multiprocessing import Pool

import numpy as np
import pandas as pd

import mc
from ngs import DATA

CORNERS = [("tt", 27, 1.80), ("ss", 100, 1.60), ("ff", -40, 1.95), ("sf", 27, 1.80), ("fs", 27, 1.80)]
TGT = {"AND": "00000001", "MAJ": "00010111", "OR": "01111111"}
N = int(sys.argv[1]) if len(sys.argv) > 1 else 100

W = pd.read_csv(DATA / "signoff_windows.csv")
TR = pd.read_csv(DATA / "signoff_trips_raw.csv").set_index("corner")


def nominal(corner):
    w = W[(W.view == "schematic") & (W.corner == corner)].iloc[0]
    t = TR.loc[corner]; d = w.delta
    u = {n: t[f"vt{n}"] - n * d for n in (1, 2, 3)}
    off = dict(AND_lo=w.AND3_lo - u[3], AND_hi=w.AND3_hi - u[2], MAJ_lo=w.MAJ3_lo - u[2],
               MAJ_hi=w.MAJ3_hi - u[1], OR_lo=w.OR3_lo - u[1])
    vbs = ((w.AND3_lo + w.AND3_hi) / 2, (w.MAJ3_lo + w.MAJ3_hi) / 2, w.OR3_lo + 0.15)
    return off, tuple(round(v, 4) for v in vbs)


def windows(row, off):
    u = {n: row[f"vt{n}"] - n * row["delta"] for n in (1, 2, 3)}
    return dict(AND=(u[3] + off["AND_lo"], u[2] + off["AND_hi"]), MAJ=(u[2] + off["MAJ_lo"], u[1] + off["MAJ_hi"]),
                OR=(u[1] + off["OR_lo"], 9.0))


def centre(win, m):
    lo, hi = win[m]
    return (lo + hi) / 2 if m != "OR" else lo + 0.15


if __name__ == "__main__":
    jobs, meta = [], {}
    for c, t, v in CORNERS:
        off, vbs = nominal(c)
        meta[c] = (off, vbs)
        jobs += [(3000 + 1000 * k + i, c, t, v, vbs) for k, (cc, _, _) in enumerate(CORNERS) if cc == c for i in range(N)]
    with Pool(10) as p:
        res = p.map(mc.sample, jobs)
    S = pd.DataFrame(res)
    S.to_csv(DATA / "calib_samples.csv", index=False)
    rows, rng = [], np.random.default_rng(7)
    for c, g in S.groupby("corner"):
        g = g.dropna(subset=["vt1", "vt2", "vt3", "delta"]).reset_index(drop=True)
        off, vbs = meta[c]
        wins = [windows(r, off) for _, r in g.iterrows()]
        # model validation against transient truth tables at the nominal V_B
        agree = []
        for r, w in zip(g.itertuples(), wins):
            for m, vb in zip(("AND", "MAJ", "OR"), vbs):
                pred = w[m][0] < vb < w[m][1]
                agree.append(pred == (getattr(r, f"tt_{m}") == TGT[m]))
        transient_yield = float(np.mean([all(getattr(r, f"tt_{m}") == TGT[m] for m in TGT) for r in g.itertuples()]))
        for bits, sig_buf in itertools.product((6, 8, 10), (0.0, 0.003, 0.005)):
            lsb = 1.25 / 2 ** bits
            ok = tot = 0
            for i, wr in enumerate(wins):              # replica i
                vb = {m: np.round(centre(wr, m) / lsb) * lsb for m in TGT}
                for j, wv in enumerate(wins):          # victim j
                    if i == j:
                        continue
                    e = rng.normal(0, sig_buf, 3) if sig_buf > 0 else np.zeros(3)
                    ok += all(wv[m][0] < vb[m] + ek < wv[m][1] for m, ek in zip(TGT, e))
                    tot += 1
            rows.append(dict(corner=c, N=len(g), bits=bits, buffer_sigma_mV=sig_buf * 1e3, pair_yield=ok / tot,
                             transient_yield_nominal=transient_yield, model_agreement=float(np.mean(agree))))
    Y = pd.DataFrame(rows)
    Y.to_csv(DATA / "calib_yield.csv", index=False)
    pd.set_option("display.width", 200)
    print(Y.round(4).to_string())
