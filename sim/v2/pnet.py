"""
Network-level p-bit benchmarks driven by SPICE-calibrated QFG p-bit cells.

Each p-bit i updates (Gibbs, sequential) as
    s_i = sgn( I_i + o_i + sigma_eff * n ),   n ~ N(0,1)
    I_i = beta_V * (sum_j J_ij s_j + h_i)
where, for the QFG cell, a weight unit is one 2x2-um coupling MIM, so the FG step per unit is
beta_V = Delta_w = k_w * VDD (taken from the transistor-level design), o_i is the per-cell trip
offset (Monte-Carlo sigma from pbit_trip_mc.csv), weights carry MIM mismatch (sigma_C/C from the
Sky130 MIM model: 1% * 2.8 / sqrt(area)), and sigma_eff is set by the injected dither amplitude
(pbit_fits.csv: sigma_eff = k_n * sigma_xi).  An "ideal" p-bit (o_i = 0, exact weights,
logistic activation) is run side by side.

Benchmarks
  1. Invertible AND gate (Camsari et al., PRX 2017): Boltzmann-distribution fidelity (KL divergence)
     in free mode and input inference with the output clamped.
  2. Max-Cut on random G(n, 0.5) and 3-regular graphs, annealed by the dither amplitude:
     approximation ratio vs. exhaustive optimum (n=20) and vs. the best of 200 SA restarts (n=64, 128).
Outputs: data/v2/pnet_*.csv
"""
from __future__ import annotations

import itertools
import math

import numpy as np
import pandas as pd

from ngs import DATA

rng0 = np.random.default_rng(2026)


# ------------------------------------------------------------------ device parameters
def load_cell():
    fits = pd.read_csv(DATA / "pbit_fits.csv")
    mc = pd.read_csv(DATA / "pbit_trip_mc.csv")
    # k_n: FG-referred sigma per volt of dither (linear fit through the origin)
    kn = float(np.sum(fits.sigma_eff * fits.sigma_xi) / np.sum(fits.sigma_xi ** 2))
    sig_off = float(mc.vt.std())
    return dict(kn=kn, sig_off=sig_off)


CIN = 9.52e-15          # one 2x2-um coupling MIM (unit weight)
C_PMOS = 23e-15         # PMOS-load gate capacitance on FG (K=3 design)
VDD_ = 1.8
SIG_MIM = 0.01 * 2.8 / math.sqrt(4.0)   # Sky130 MIM model mismatch, 2x2 um cap (relative)


class PNet:
    """Sequential-Gibbs network of QFG p-bits.

    Neuron i couples |J_ij| unit MIMs from neighbour j (from Y or YB depending on sign) plus one
    unit noise MIM, so C_FG,i = CIN*(sum_j|J_ij| + 1) + C_PMOS and the bipolar FG step per unit weight
    is dw_i = 0.5*CIN*VDD/C_FG,i.  The dither line (amplitude sigma_xi) gives an FG noise
    sigma_i = (CIN/C_FG,i)*sigma_xi = dw_i * T with T = 2*sigma_xi/VDD, i.e. the same dimensionless
    temperature T for every neuron.  Cell non-idealities enter as the trip offset o_i (V, from the
    transistor-level Monte Carlo), expressed in weight units o_i/dw_i, and as MIM weight mismatch.
    """

    def __init__(self, J, h, cell=None, mismatch=True, trim=False, rng=rng0, logistic=False):
        self.logistic = logistic
        self.n = len(h)
        self.J, self.h = np.array(J, float), np.array(h, float)
        units = np.abs(self.J).sum(1) + 1
        self.dw = 0.5 * CIN * VDD_ / (CIN * units + C_PMOS)
        if cell is not None and mismatch:
            err = rng.normal(0, SIG_MIM, self.J.shape) / np.sqrt(np.maximum(np.abs(self.J), 1))
            self.Jr = self.J * (1 + err)          # row i = caps on neuron i's FG (not symmetric)
            off_v = rng.normal(0, cell["sig_off"], self.n)
            if trim:   # one-time per-cell VB trim with a 1-mV DAC (residual uniform +-0.5 mV)
                off_v = rng.uniform(-0.5e-3, 0.5e-3, self.n)
            self.off = off_v / self.dw            # in weight units
        else:
            self.Jr, self.off = self.J.copy(), np.zeros(self.n)

    def sweep(self, s, T, rng):
        """One sequential sweep at dimensionless temperature T (FG noise / unit weight step)."""
        for i in rng.permutation(self.n):
            I = self.Jr[i] @ s + self.h[i] + self.off[i]
            if self.logistic:   # textbook p-bit, slope-matched to the Gaussian-dither cell
                p = 1.0 / (1.0 + math.exp(-2.0 * I * 0.7979 / T))
            else:               # QFG cell: Gaussian dither -> erf activation
                p = 0.5 * (1.0 + math.erf(I / (T * math.sqrt(2.0))))
            s[i] = 1 if rng.random() < p else -1
        return s


# ------------------------------------------------------------------ invertible AND
J_AND = np.array([[0, -1, 2], [-1, 0, 2], [2, 2, 0]], float)
H_AND = np.array([1, 1, -2], float)


def boltzmann(J, h, beta):
    states = np.array(list(itertools.product([-1, 1], repeat=len(h))))
    E = -0.5 * np.einsum("ki,ij,kj->k", states, J, states) - states @ h
    w = np.exp(-beta * E); return states, w / w.sum()


def and_benchmark(cell, sweeps=20000, T=0.798, rng=rng0):
    """Invertible AND at beta = 1 (T = 0.798 is the slope-matched Gaussian width).
    Reference: exact Boltzmann distribution at beta = 1."""
    beta = 0.7979 / T
    states, pb = boltzmann(J_AND, H_AND, beta=beta)
    rows, dists = [], []
    for label, kw in [("ideal logistic p-bit", dict(cell=None, logistic=True)),
                      ("ideal Gaussian-dither p-bit", dict(cell=None)),
                      ("QFG cell (mismatch)", dict(cell=cell, mismatch=True)),
                      ("QFG cell (trimmed)", dict(cell=cell, mismatch=True, trim=True))]:
        kl_list, clamp_ok = [], []
        for inst in range(10 if kw.get("cell") else 3):
            net = PNet(J_AND, H_AND, rng=np.random.default_rng(100 + inst), **kw)
            s = rng.choice([-1, 1], 3).astype(float)
            cnt = {tuple(st): 0 for st in states}
            for t in range(sweeps):
                s = net.sweep(s, T, rng)
                cnt[tuple(s.astype(int))] += 1
            p = np.array([cnt[tuple(st)] for st in states], float); p /= p.sum()
            kl_list.append(float(np.sum(np.where(p > 0, p * np.log(p / pb), 0))))
            if inst == 0:
                dists.append(dict(model=label, **{"".join("1" if v > 0 else "0" for v in st): pp for st, pp in zip(states, p)}))
            # clamp output C to +1 (logic 1): inputs must settle to (1,1)
            net.h = H_AND + np.array([0, 0, 10.0])
            s = rng.choice([-1, 1], 3).astype(float); hit = 0
            for t in range(5000):
                s = net.sweep(s, T, rng)
                hit += int(s[0] == 1 and s[1] == 1)
            clamp_ok.append(hit / 5000)
        rows.append(dict(model=label, KL_mean=np.mean(kl_list), KL_max=np.max(kl_list),
                         clamp_inference_mean=np.mean(clamp_ok), clamp_inference_min=np.min(clamp_ok)))
    dists.append(dict(model="Boltzmann", **{"".join("1" if v > 0 else "0" for v in st): pp for st, pp in zip(states, pb)}))
    pd.DataFrame(dists).to_csv(DATA / "pnet_and_dist.csv", index=False)
    return pd.DataFrame(rows), states, pb


# ------------------------------------------------------------------ Max-Cut
def random_graph(n, kind, rng):
    if kind == "G(n,0.5)":
        A = (rng.random((n, n)) < 0.5).astype(float)
        A = np.triu(A, 1); return A + A.T
    # random 3-regular via configuration model with rejection
    while True:
        stubs = np.repeat(np.arange(n), 3); rng.shuffle(stubs)
        e = stubs.reshape(-1, 2)
        if np.any(e[:, 0] == e[:, 1]): continue
        A = np.zeros((n, n))
        ok = True
        for a, b in e:
            if A[a, b]: ok = False; break
            A[a, b] = A[b, a] = 1
        if ok: return A


def cut_value(A, s):
    return 0.25 * np.sum(A * (1 - np.outer(s, s)))


def maxcut_exact(A):
    n = len(A); best = 0
    # enumerate with s0 fixed (symmetry); vectorised in chunks
    idx = np.arange(1 << (n - 1))
    for c0 in range(0, len(idx), 1 << 16):
        b = idx[c0:c0 + (1 << 16)]
        S = np.ones((len(b), n)); S[:, 1:] = 1 - 2 * ((b[:, None] >> np.arange(n - 1)) & 1)
        cuts = 0.25 * (A.sum() - np.einsum("ki,ij,kj->k", S, A, S))
        best = max(best, cuts.max())
    return best


def anneal(net, A, sweeps, rng, s_hi=None, s_lo=0.15):
    """Anneal the dither amplitude: T from s_hi down to s_lo (geometric); s_hi ~ sqrt(degree)."""
    s_hi = s_hi or 2.0 * math.sqrt(A.sum(1).mean())
    s = rng.choice([-1, 1], net.n).astype(float); best = 0
    for t in range(sweeps):
        sig = s_hi * (s_lo / s_hi) ** (t / max(sweeps - 1, 1))
        s = net.sweep(s, sig, rng)
        best = max(best, cut_value(A, s))
    return best


def sa_reference(A, sweeps, restarts, rng):
    best = 0
    for r in range(restarts):
        net = PNet(-A, np.zeros(len(A)))
        best = max(best, anneal(net, A, sweeps, rng))
    return best


def maxcut_benchmark(cell, rng=rng0):
    rows = []
    for n, kind, ref in [(20, "G(n,0.5)", "exact"), (20, "3-regular", "exact"),
                         (64, "G(n,0.5)", "SA"), (64, "3-regular", "SA")]:
        for g in range(5):
            A = random_graph(n, kind, np.random.default_rng(1000 * n + g))
            opt = maxcut_exact(A) if ref == "exact" else sa_reference(A, 1000, 50, np.random.default_rng(7 + g))
            for label, kw in [("ideal", dict(cell=None, logistic=True)), ("QFG cell (mismatch)", dict(cell=cell, mismatch=True)),
                              ("QFG cell (trimmed)", dict(cell=cell, mismatch=True, trim=True))]:
                for sweeps in (100, 1000):
                    vals = []
                    for r in range(10):
                        net = PNet(-A, np.zeros(n), rng=np.random.default_rng(r + 31 * g), **kw)
                        vals.append(anneal(net, A, sweeps, np.random.default_rng(500 + r)))
                    vals = np.array(vals)
                    rows.append(dict(n=n, graph=kind, g=g, reference=ref, opt=opt, model=label, sweeps=sweeps,
                                     ratio_mean=vals.mean() / opt, ratio_best=vals.max() / opt,
                                     p_success=float(np.mean(vals >= opt))))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    cell = load_cell()
    print("cell:", cell, "SIG_MIM", SIG_MIM)
    andres, states, pb = and_benchmark(cell)
    andres.to_csv(DATA / "pnet_and.csv", index=False)
    print(andres.round(4).to_string())
    mc = maxcut_benchmark(cell)
    mc.to_csv(DATA / "pnet_maxcut.csv", index=False)
    print(mc.groupby(["n", "graph", "model", "sweeps"]).agg(ratio=("ratio_mean", "mean"), best=("ratio_best", "mean"),
                                                             p_succ=("p_success", "mean")).round(3).to_string())
