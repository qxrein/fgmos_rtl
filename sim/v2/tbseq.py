"""
Single-cell sequential testbench: reset -> evaluate, once per minterm.

One physical cell (one mismatch draw) sees all eight minterms, so this bench
is used for Monte Carlo, transient timing/energy and corner sign-off.
Cycle k (k = 0..7):  [RST high, inputs low  : T_R ns]
                     [RST low,  inputs = m_k: T_E ns]  -> sample at end
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ngs import VDD, cell_subckt, header, parse_kv, run
from tb import MINTERMS, TARGETS_Y

T_R = 1.0     # reset phase (ns)
T_E = 3.0     # evaluation phase (ns)
T_EDGE = 0.05


def _pwl_inputs(vdd: float, order=range(8), t_p=None):
    """PWL for A,B,C and RST over the 8-cycle sequence.
    t_p: return-to-zero input pulse width (ns); None = inputs held until the end of evaluation."""
    tcyc = T_R + T_E
    rst, a, b, c = [(0, vdd)], [(0, 0)], [(0, 0)], [(0, 0)]
    for k, m in enumerate(order):
        t0 = k * tcyc
        bits = MINTERMS[m]
        # reset high during [t0, t0+T_R], low during evaluation
        rst += [(t0 + T_R, vdd), (t0 + T_R + T_EDGE, 0), (t0 + tcyc - T_EDGE, 0), (t0 + tcyc, vdd)]
        for lst, bit in zip((a, b, c), bits):
            v = vdd * bit
            ti = t0 + T_R + 2 * T_EDGE        # inputs rise after reset is released
            te = (t0 + tcyc - 2 * T_EDGE) if t_p is None else (ti + T_EDGE + t_p)
            lst += [(ti, 0), (ti + T_EDGE, v), (te, v), (te + T_EDGE, 0)]
    f = lambda pts: "PWL(" + " ".join(f"{t:.4f}n {v:.4f}" for t, v in pts) + ")"
    return f(rst), f(a), f(b), f(c), 8 * tcyc


def seq_deck(params=None, corner="tt", temp=27.0, vdd=VDD, vbs=(0.1, 0.4, 0.8),
             mc=False, seed=None, cload_ff=5.0, save_wave=False, cell_text=None, t_p=None) -> str:
    rst, a, b, c, tstop = _pwl_inputs(vdd, t_p=t_p)
    tcyc = T_R + T_E
    meas, echo = [], ["vb=$vbv"]
    for k in range(8):
        ts = k * tcyc + (T_R + T_E - 0.2 if t_p is None else T_R + 3 * T_EDGE + t_p - 0.03)
        meas += [f"meas tran y{k}v FIND v(y) AT={ts:.4f}n",
                 f"meas tran yb{k}v FIND v(yb) AT={ts:.4f}n",
                 f"meas tran fg{k}v FIND v(fg) AT={ts:.4f}n"]
        echo += [f"y{k}=$&y{k}v", f"yb{k}=$&yb{k}v", f"fg{k}=$&fg{k}v"]
    # supply energy over the whole 8-cycle sequence
    meas += [f"meas tran eavg INTEG i(Vdd) FROM=0 TO={tstop}n"]
    echo += ["q=$&eavg"]
    seed_line = f"set rndseed={seed}" if seed is not None else ""
    vb_list = " ".join(f"{v:.4f}" for v in vbs)
    wave = ""
    if save_wave:
        wave = "  set fname = wave_{$vbv}.txt\n  wrdata $fname v(rst) v(a) v(b) v(c) v(fg) v(yb) v(y) i(Vdd)\n"
    return header(corner, temp, mc) + (cell_text or cell_subckt(params)) + f"""
Vdd vdd 0 {vdd}
Vrst rst 0 {rst}
Va a 0 {a}
Vb b 0 {b}
Vc c 0 {c}
Vvb vb 0 0.5
X1 a b c rst vb y yb fg vdd 0 QFG_TLG
CL y 0 {cload_ff}f
.option method=gear reltol=1e-4
.control
{seed_line}
set wr_singlescale
set wr_vecnames
foreach vbv {vb_list}
  alter Vvb dc = $vbv
  let vbv = $vbv
  tran 10p {tstop}n
{chr(10).join('  ' + x for x in meas)}
  echo "{' '.join(echo)}" >> out.txt
{wave}  destroy all
end
.endc
.end
"""


def seq_run(params=None, tag="seq", **kw) -> pd.DataFrame:
    _, d = run(seq_deck(params, **kw), tag=tag)
    df = pd.DataFrame(parse_kv(d / "out.txt"))
    df.attrs["dir"] = str(d)
    return df


def truth(df_row, vdd=VDD, node="y") -> str:
    hi, lo = 0.8 * vdd, 0.2 * vdd
    return "".join("1" if df_row[f"{node}{k}"] >= hi else ("0" if df_row[f"{node}{k}"] <= lo else "x")
                   for k in range(8))
