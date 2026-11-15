"""
Transistor-level p-bit characterisation of the QFG primitive (Sky130 BSIM4, TT 27 C).

1. Intrinsic noise: integrated kT/C on FG (reset switch ON) and FG-referred noise of the
   decision stage at its trip point, both from ngspice .noise.
2. Sigmoids: P(m=1) vs VB for injected per-cycle Gaussian dither xi on the NZ coupling input
   (sigma_xi in {25, 50, 100, 200} mV), 300 reset/evaluate cycles per bias point.
   Fit P = Phi((VB - V*)/sigma_eff); compare sigma_eff with k_n*sigma_xi (capacitive divider).
3. Bit-stream statistics at P ~= 0.5 (2000 cycles): lag-k autocorrelation, runs test.
4. Mismatch: DC trip V* of the decision stage over 200 Monte Carlo draws.
Outputs in data/v2/pbit_*.csv
"""
from __future__ import annotations

from math import erf, sqrt
from multiprocessing import Pool

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.stats import norm

from ngs import DATA, VDD, header, parse_kv, run
from pbit import noise_comp, noise_ktc, pbit_subckt, sigmoid_run

KB, T = 1.380649e-23, 300.15


def trip_dc(mc=False, seed=None, Nw=2):
    deck = header("tt", 27.0, mc, seed) + pbit_subckt(None, Nw=Nw) + f"""
Vdd vdd 0 {VDD}
Ven en 0 {VDD}
Vrst rst 0 {VDD}
Vvb vb 0 0.5
X1 {' '.join('0' for _ in range(Nw))} 0 en rst vb y yb fg vdd 0 QFG_PB
.control
dc Vvb 0 1.4 0.0005
meas dc vt WHEN v(yb)={VDD/2} CROSS=1
echo "vt=$&vt" > out.txt
.endc
.end
"""
    _, d = run(deck, tag="pbtrip")
    return parse_kv(d / "out.txt")[0]["vt"]


def sig_job(args):
    vb, s, seed = args
    df = sigmoid_run(vb, s, n_cyc=300, seed=seed, tag="pbsig")
    return dict(vb=vb, sigma_xi=s, p1=df.bit.mean(), n=len(df), fg_mean=df.fg.mean())


def fit(vb, p):
    f = lambda x, v0, s: norm.cdf((x - v0) / s)
    (v0, s), _ = curve_fit(f, vb, p, p0=[np.median(vb), 0.02], maxfev=20000)
    return v0, abs(s)


if __name__ == "__main__":
    out = {}
    # --- 1. intrinsic noise
    vt0 = trip_dc()
    vn_ktc = noise_ktc()
    nc = noise_comp(vt0)
    # NZ coupling ratio k_n from a DC-free estimate: step NZ by 1 V in a short transient
    out.update(dict(vtrip_nom=vt0, vn_ktc_V=vn_ktc, vn_comp_in_V=nc["vin"], vn_comp_out_V=nc["von"]))
    print("trip", vt0, "kTC noise", vn_ktc, "comp", nc)
    # --- 4. mismatch of V* (decision-stage trip)
    with Pool(10) as p:
        vts = p.starmap(trip_dc, [(True, 5000 + i) for i in range(200)])
    pd.DataFrame({"vt": vts}).to_csv(DATA / "pbit_trip_mc.csv", index=False)
    out.update(dict(vt_mc_mean=float(np.mean(vts)), vt_mc_sigma=float(np.std(vts))))
    print("V* MC: mean %.4f sigma %.2f mV" % (np.mean(vts), np.std(vts) * 1e3))
    # --- 2. sigmoids (the FG sees k_n*xi; scan VB around the trip point)
    jobs = []
    for s in (0.025, 0.05, 0.1, 0.2):
        span = max(0.02, 0.5 * s)   # FG-referred sigma ~ k_n*s, k_n ~ 0.1-0.2
        for i, vb in enumerate(np.linspace(vt0 - span, vt0 + span, 13)):
            jobs.append((round(float(vb), 5), s, 100 + i))
    with Pool(10) as p:
        rows = p.map(sig_job, jobs)
    S = pd.DataFrame(rows)
    S.to_csv(DATA / "pbit_sigmoid.csv", index=False)
    fits = []
    for s, g in S.groupby("sigma_xi"):
        v0, se = fit(g.vb.to_numpy(), g.p1.to_numpy())
        fits.append(dict(sigma_xi=s, v_half=v0, sigma_eff=se))
    F = pd.DataFrame(fits)
    F.to_csv(DATA / "pbit_fits.csv", index=False)
    print(F.round(5).to_string())
    # --- 3. long bit stream at P~0.5 for the 100 mV case
    v_half = float(F.loc[F.sigma_xi == 0.1, "v_half"].iloc[0])
    with Pool(8) as p:
        parts = p.starmap(sigmoid_run, [(v_half, 0.1, 250, None, "tt", 27.0, VDD, 900 + j) for j in range(8)])
    bits = np.concatenate([pp.bit.to_numpy() for pp in parts])
    pd.DataFrame({"bit": bits}).to_csv(DATA / "pbit_stream.csv", index=False)
    x = bits - bits.mean()
    ac = [float(np.dot(x[:-k], x[k:]) / np.dot(x, x)) for k in range(1, 21)]
    n1, n0 = bits.sum(), len(bits) - bits.sum()
    runs = 1 + int(np.sum(bits[1:] != bits[:-1]))
    mu = 2 * n1 * n0 / len(bits) + 1
    var = (mu - 1) * (mu - 2) / (len(bits) - 1)
    z = (runs - mu) / sqrt(var)
    out.update(dict(stream_len=len(bits), p1=float(bits.mean()), lag1=ac[0], max_abs_ac=float(np.max(np.abs(ac))),
                    ci95=1.96 / sqrt(len(bits)), runs_z=z))
    pd.DataFrame({"lag": range(1, 21), "ac": ac}).to_csv(DATA / "pbit_autocorr.csv", index=False)
    pd.Series(out).to_csv(DATA / "pbit_summary.csv")
    print(pd.Series(out).to_string())
