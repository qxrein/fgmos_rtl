"""
Floating-gate retention analysis (reviewer request: retention/leakage).

During evaluation the FG node is isolated: the only DC paths are the OFF reset
switch MR (subthreshold + junction/GIDL, as modelled by Sky130 BSIM4) and the
PMOS gate (gate tunnelling is disabled in the Sky130 models: igcmod=igbmod=0,
so we bound it separately in the paper).  We force the FG voltage with an
ideal source, measure the leakage current I_leak(V_FG) at several PVT points,
and integrate dV/dt = -I_leak/C_FG to obtain the hold time before the FG drifts
by a given fraction of the programming margin.
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from ngs import DATA, VDD, cell_subckt, header, parse_kv, pex_cell_text, run


def leak_curve(params, vb, corner="tt", temp=27.0, vdd=VDD, n_on=0, K=3,
               v_lo=-0.2, v_hi=1.8, step=0.02, pex=True):
    """pex=True uses the Magic-extracted cell, whose devices carry layout AD/AS/PD/PS, so the
    reset-switch drain junction leakage is included (schematic devices have zero junction area)."""
    ins = " ".join(("vdd" if i < n_on else "0") for i in range(K))
    cell = pex_cell_text() if (pex and K == 3 and params is None) else cell_subckt(params, K=K)
    deck = header(corner, temp) + cell + f"""
Vdd vdd 0 {vdd}
Vrst rst 0 0
Vvb vb 0 {vb}
Vfg fgx 0 {vb}
* ammeter: current flowing from the forcing source INTO the FG node
Vam fgx fg 0
X1 {ins} rst vb y yb fg vdd 0 {'QFG_TLG' if K == 3 else f'QFG_TLG{K}'}
.option gmin=1e-18 abstol=1e-17 reltol=1e-4 itl1=500 itl2=500
.control
set wr_singlescale
set wr_vecnames
dc Vfg {v_lo} {v_hi} {step}
wrdata leak.txt i(Vam)
.endc
.end
"""
    _, d = run(deck, tag=f"leak_{corner}_{int(temp)}")
    a = np.loadtxt(d / "leak.txt", skiprows=1)
    # i(Vam) > 0 means current flows into FG from the source, i.e. the node
    # would otherwise *lose* that charge to leakage paths.
    return pd.DataFrame({"vfg": a[:, 0], "i_leak": a[:, 1]})


def hold_time(curve: pd.DataFrame, v0: float, c_fg: float, dv: float, t_max=1e4):
    """Integrate dV/dt = -I(V)/C from V0 until |V-V0| >= dv (s)."""
    v, t = v0, 0.0
    vf, il = curve.vfg.to_numpy(), curve.i_leak.to_numpy()
    for _ in range(200000):
        i = np.interp(v, vf, il)
        if abs(i) < 1e-30:
            return np.inf
        # adaptive step: move 0.1 mV per step
        dvdt = -i / c_fg
        h = min(1e-4 / abs(dvdt), t_max)
        v += dvdt * h
        t += h
        if abs(v - v0) >= dv:
            return t
        if t >= t_max:
            return np.inf
    return t


def _job(args):
    corner, temp, mode, vb, n_on, C_FG, DELTA, budgets = args
    c = leak_curve(None, vb, corner, temp, n_on=n_on)
    c["corner"], c["temp"], c["mode"], c["n_on"] = corner, temp, mode, n_on
    v0 = vb + n_on * DELTA          # FG right after evaluation starts
    i0 = float(np.interp(v0, c.vfg, c.i_leak))
    r = dict(corner=corner, temp=temp, mode=mode, n_on=n_on, vfg0=v0, i_leak_A=i0, drift_V_per_s=-i0 / C_FG)
    for b in budgets:
        r[f"t_hold_{int(b*1e3)}mV_s"] = hold_time(c, v0, C_FG, b)
    return r, c


if __name__ == "__main__":
    from multiprocessing import Pool
    C_IN, DELTA = 9.52e-15, 0.167
    C_FG = C_IN * 1.8 / DELTA
    budgets = (0.010, 0.050)
    jobs = [(corner, temp, mode, vb, n_on, C_FG, DELTA, budgets)
            for corner, temp in [("tt", 27), ("tt", 85), ("tt", 125), ("ff", 27), ("ff", 125), ("ss", 125)]
            for mode, vb in (("AND3", 0.307), ("MAJ3", 0.571), ("OR3", 0.849)) for n_on in (0, 3)]
    with Pool(4) as p:
        res = p.map(_job, jobs)
    pd.concat([c for _, c in res]).to_csv(DATA / "retention_curves.csv", index=False)
    df = pd.DataFrame([r for r, _ in res])
    df.to_csv(DATA / "retention.csv", index=False)
    print(df.to_string())
    print("C_FG = %.1f fF" % (C_FG * 1e15))
