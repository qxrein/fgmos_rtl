"""
Build every figure, table and in-text number of the IOP manuscript from the result files in data/v2.
Run after the simulation campaign:  python make_paper_assets.py
Writes paper_iop/numbers.tex, paper_iop/tables/*.tex, paper_iop/figures/*.pdf
"""
from __future__ import annotations

import re
import shutil
from math import sqrt
from pathlib import Path

import matplotlib
import matplotlib.ticker
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data/v2"
P = ROOT / "paper_iop"
FIG = P / "figures"
TAB = P / "tables"
for d in (FIG, TAB):
    d.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({"font.family": "sans-serif", "font.size": 8, "axes.labelsize": 8, "legend.fontsize": 7,
                     "xtick.labelsize": 7, "ytick.labelsize": 7, "axes.linewidth": 0.6, "lines.linewidth": 1.0,
                     "savefig.bbox": "tight", "pdf.fonttype": 42})
W1, W2 = 8.5 / 2.54, 15.0 / 2.54     # IOP single / double column widths (in)
N = {}                                 # \newcommand numbers


def mv(x):   return f"\\SI{{{x*1e3:.0f}}}{{\\milli\\volt}}"
def ps(x):   return f"\\SI{{{x:.0f}}}{{\\pico\\second}}"
def fj(x):   return f"\\SI{{{x:.0f}}}{{\\femto\\joule}}"


# ------------------------------------------------------------------ design / layout
bbox = (-0.8, 0.0, 9.6, 14.97)
N["CellW"] = f"{bbox[2]-bbox[0]:.1f}"
N["CellH"] = f"{bbox[3]-bbox[1]:.2f}"
cell_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
N["CellArea"] = f"{cell_area:.0f}"
N["PDKhash"] = "c6d73a3"

# extracted FG parasitics (top-level coupling caps touching FG, excluding the MIM devices)
pex = (ROOT / "layout/v2/magic/qfg_tlg_pex.spice").read_text()
top = pex[pex.index(".subckt qfg_tlg "):]
fgc, fgyb = 0.0, 0.0
for ln in top.splitlines():
    m = re.match(r"^C\d+\s+(\S+)\s+(\S+)\s+([\d.eE+-]+)f", ln)
    if m and "FG" in (m.group(1), m.group(2)):
        fgc += float(m.group(3))
        if "YB" in (m.group(1), m.group(2)):
            fgyb = float(m.group(3))
N["FGparasitic"] = f"\\SI{{{fgc:.1f}}}{{\\femto\\farad}}"
N["FGYBcoupling"] = f"\\SI{{{fgyb:.2f}}}{{\\femto\\farad}}"

# ------------------------------------------------------------------ sign-off windows / replica
W = pd.read_csv(D / "signoff_windows.csv")
V = pd.read_csv(D / "signoff2_vb.csv")
tt_p = W[(W.view == "pex") & (W.corner == "tt")].iloc[0]
N["WinTTAND"] = mv(tt_p.AND3_w); N["WinTTMAJ"] = mv(tt_p.MAJ3_w); N["WinTTOR"] = mv(tt_p.OR3_w)
N["DeltaTT"] = f"\\SI{{{tt_p.delta*1e3:.0f}}}{{\\milli\\volt}}"
CFG = 9.52e-15 * 1.8 / tt_p.delta
N["CFG"] = f"\\SI{{{CFG*1e15:.0f}}}{{\\femto\\farad}}"
shift = 0.0
for c in W.corner.unique():
    s = W[(W.view == "schematic") & (W.corner == c)].iloc[0]; p_ = W[(W.view == "pex") & (W.corner == c)].iloc[0]
    for k in ("AND3_lo", "AND3_hi", "MAJ3_lo", "MAJ3_hi", "OR3_lo"):
        shift = max(shift, abs(s[k] - p_[k]))
N["MaxWinShiftPEX"] = mv(shift)
mA = min(V.margin_AND_schematic.min(), V.margin_AND_pex.min())
mM = min(V.margin_MAJ_schematic.min(), V.margin_MAJ_pex.min())
mO = min(V.margin_OR_schematic.min(), V.margin_OR_pex.min())
N["MinMarginAND"], N["MinMarginMAJ"], N["MinMarginOR"] = mv(mA), mv(mM), mv(mO)
N["MinMarginAll"] = mv(min(mA, mM, mO))

order = ["tt", "ss", "ff", "sf", "fs"]
cname = {"tt": "TT, 27\\,\\si{\\celsius}, 1.80\\,V", "ss": "SS, 100\\,\\si{\\celsius}, 1.60\\,V",
         "ff": "FF, $-$40\\,\\si{\\celsius}, 1.95\\,V", "sf": "SF, 27\\,\\si{\\celsius}, 1.80\\,V",
         "fs": "FS, 27\\,\\si{\\celsius}, 1.80\\,V"}
with open(TAB / "tab_signoff.tex", "w") as f:
    f.write("\\begin{table}\n\\caption{Programming windows of $V_B$ (V) at five PVT corners, schematic (S) and extracted (X) views, "
            "and replica-referenced programming voltages (equation~(\\ref{eq:replica})). OR3 windows extend beyond the "
            "\\SI{1.25}{\\volt} sweep limit.}\n\\label{tab:signoff}\n\\centering\\small\n"
            "\\begin{tabular}{l l c c c c c c c}\n\\toprule\n"
            "Corner & View & \\multicolumn{2}{c}{AND3} & \\multicolumn{2}{c}{MAJ3} & OR3 & $\\Delta$ (mV) & $V_B$ (AND/MAJ/OR) \\\\\n"
            " & & low & high & low & high & low & & \\\\\n\\midrule\n")
    for c in order:
        v = V[V.corner == c].iloc[0]
        for i, view in enumerate(("schematic", "pex")):
            r = W[(W.view == view) & (W.corner == c)].iloc[0]
            lab = cname[c] if i == 0 else ""
            vb = f"{v.vb_AND:.3f} / {v.vb_MAJ:.3f} / {v.vb_OR:.3f}" if i == 0 else ""
            f.write(f"{lab} & {'S' if view=='schematic' else 'X'} & {r.AND3_lo:.2f} & {r.AND3_hi:.2f} & {r.MAJ3_lo:.2f} & "
                    f"{r.MAJ3_hi:.2f} & {r.OR3_lo:.2f} & {r.delta*1e3:.0f} & {vb} \\\\\n")
    f.write("\\bottomrule\n\\end{tabular}\n\\end{table}\n")

# ------------------------------------------------------------------ timing
T = pd.read_csv(D / "signoff2_timing.csv", dtype={"truth": str})
Ts = T[T.run == "sized"]
g = Ts.groupby(["corner", "view", "mode"]).agg(tp=("t_p_ns", "first"), truth=("truth", "first"), E=("E_fJ", "mean"),
                                               tpd=("tpd_ps", "max"), trst=("trst_ps", "max"), I=("I_static_uA", "max"))
tgt = {"AND3": "00000001", "MAJ3": "00010111", "OR3": "01111111"}
ok_all = all(g.loc[idx, "truth"] == tgt[idx[2]] for idx in g.index)
N["TpFactor"] = "1.5 times"
xt = g.xs(("tt", "pex"), level=("corner", "view"))
N["TpdTTmax"] = ps(xt.tpd.max())
N["ETTAND"], N["ETTMAJ"], N["ETTOR"] = fj(xt.loc["AND3", "E"]), fj(xt.loc["MAJ3", "E"]), fj(xt.loc["OR3", "E"])
N["ETTmin"], N["ETTmax"] = f"{xt.E.min():.0f}", fj(xt.E.max())
N["IstatMax"] = f"\\SI{{{g.I.max():.0f}}}{{\\micro\\ampere}}"
with open(TAB / "tab_timing.tex", "w") as f:
    f.write("\\begin{table}\n\\caption{Worst-case propagation delay, mean energy per operation "
            "(averaged over the eight minterms) with return-to-zero input pulses of width $t_p$; "
            "S = schematic, X = extracted. All truth tables were correct"
            + ("" if ok_all else " except where marked") + ".}\n\\label{tab:timing}\n\\centering\\small\n"
            "\\begin{tabular}{l c l r r r r r r}\n\\toprule\n"
            "Corner & $t_p$ (ns) & Mode & \\multicolumn{2}{c}{$t_\\mathrm{pd}$ (ps)} & \\multicolumn{2}{c}{$E$ (fJ/op)} & "
            "\\multicolumn{2}{c}{$I_\\mathrm{static,max}$ (\\si{\\micro\\ampere})} \\\\\n & & & S & X & S & X & S & X \\\\\n\\midrule\n")
    for c in order:
        for j, mode in enumerate(("AND3", "MAJ3", "OR3")):
            s = g.loc[(c, "schematic", mode)]; x = g.loc[(c, "pex", mode)]
            mark = "" if (s.truth == tgt[mode] and x.truth == tgt[mode]) else "$^\\dagger$"
            f.write(f"{c.upper() if j==0 else ''} & {(f'{x.tp:.2f}') if j==0 else ''} & {mode}{mark} & {s.tpd:.0f} & {x.tpd:.0f} & "
                    f"{s.E:.0f} & {x.E:.0f} & {s.I:.0f} & {x.I:.0f} \\\\\n")
        if c != order[-1]:
            f.write("\\addlinespace\n")
    f.write("\\bottomrule\n\\end{tabular}\n\\end{table}\n")

# ------------------------------------------------------------------ Monte Carlo
mcf = D / "mc_tt.csv"
mc = pd.read_csv(mcf, dtype={"tt_AND": str, "tt_MAJ": str, "tt_OR": str})
mc = mc[mc.get("error").isna()] if "error" in mc else mc
ok = ((mc.tt_AND == "00000001") & (mc.tt_MAJ == "00010111") & (mc.tt_OR == "01111111"))
N["MCyield"] = f"{ok.sum()}/{len(mc)}"
sig = [mc[f"vt{n}"].std() for n in (1, 2, 3)]
N["MCsigVt"] = f"\\SIrange{{{min(sig)*1e3:.1f}}}{{{max(sig)*1e3:.1f}}}{{\\milli\\volt}}"
N["MCsigDelta"] = f"\\SI{{{mc.delta.std()*1e3:.1f}}}{{\\milli\\volt}}"
N["MarginSigma"] = f"{min(mA, mM, mO)/max(sig):.0f}"

# ------------------------------------------------------------------ retention
R = pd.read_csv(D / "retention.csv")
r27 = R[(R.corner == "tt") & (R.temp == 27)]
N["DriftTT"] = f"\\SI{{{abs(r27.drift_V_per_s).max()*1e3:.0f}}}{{\\milli\\volt\\per\\second}}"
N["HoldTTfifty"] = f"\\SI{{{r27.t_hold_50mV_s.min():.0f}}}{{\\second}}"
hot = R[R.temp == 125]
h10 = hot.t_hold_10mV_s.min()
N["HoldHotTen"] = (f"\\SI{{{h10*1e3:.0f}}}{{\\milli\\second}}" if h10 < 1 else f"\\SI{{{h10:.1f}}}{{\\second}}")
ref = R.t_hold_10mV_s.min()
_r = ref / 2
N["RefreshRec"] = (f"\\SI{{{np.floor(_r*1e6/10)*10:.0f}}}{{\\micro\\second}}" if _r < 1e-3 else
                   f"\\SI{{{np.floor(_r*1e3):.0f}}}{{\\milli\\second}}" if _r < 1 else f"\\SI{{{np.floor(_r):.0f}}}{{\\second}}")
N["HoldHotTen"] = (f"\\SI{{{h10*1e6:.0f}}}{{\\micro\\second}}" if h10 < 1e-3 else N["HoldHotTen"])

# ------------------------------------------------------------------ comparison / fan-in
base = {}
for ln in (D / "openroad_baselines.txt").read_text().splitlines():
    p_ = ln.split()
    base[p_[0]] = dict(area=float(p_[1].split("=")[1]), delay=float(p_[4].split("=")[1]) * 1e3,
                       E=float(p_[5].split("=")[1]) / 100e6 * 1e15)
K = pd.read_csv(D / "kscale_windows.csv")
core = dict(l.split() for l in (D / "openroad_core_area.txt").read_text().splitlines())
core = {k: float(v) for k, v in core.items()}
q3 = xt
N["DelayGainThree"] = f"{base['recfg3_mux']['delay']/q3.tpd.max():.1f}$\\times$"
N["AreaPenaltyThree"] = f"{cell_area/base['recfg3_mux']['area']:.1f}$\\times$"
# measured K=5 / K=9 layouts (bounding boxes from Magic) and extracted timing at TT
KAREA = {3: cell_area, 5: (19.865 + 0.8) * 14.97, 9: (34.265 + 0.8) * 14.97}
KP = pd.read_csv(D / "kpex_timing.csv")
KW = pd.read_csv(D / "kpex_windows.csv")
KX = {}
for k in (5, 9):
    x = KP[(KP.K == k) & (KP.view == "pex")]
    KX[k] = dict(tpd=x.tpd_ps.max(), Emin=x.E_avg_fJ.min(), Emax=x.E_avg_fJ.max(), tp=x.t_p.iloc[0], ok=bool(x.ok.all()),
                 minw=KW[(KW.K == k) & (KW.view == "pex")].width.min(),
                 shift=float(np.max(np.abs(KW[(KW.K == k) & (KW.view == "pex")].set_index("T")[["lo"]].values -
                                         KW[(KW.K == k) & (KW.view == "schematic")].set_index("T")[["lo"]].values))))
k9 = KX[9]
N["KfiveArea"] = f"\\SI{{{KAREA[5]:.0f}}}{{\\micro\\metre\\squared}}"
N["KnineArea"] = f"\\SI{{{KAREA[9]:.0f}}}{{\\micro\\metre\\squared}}"
N["KnineDelay"] = ps(k9["tpd"])
N["KnineTp"] = f"\\SI{{{k9['tp']:.1f}}}{{\\nano\\second}}"
N["KnineWin"] = mv(k9["minw"])
N["KpexShift"] = mv(max(KX[5]["shift"], KX[9]["shift"]))
N["DelayGainNine"] = f"{base['thr9']['delay']/k9['tpd']:.1f}$\\times$"
N["EnergyGainNine"] = f"{base['thr9']['E']/k9['Emax']:.1f}--{base['thr9']['E']/k9['Emin']:.0f}$\\times$"
N["AreaVsCellsNine"] = f"{KAREA[9]/base['thr9']['area']:.1f}$\\times$"
N["AreaVsCoreNine"] = f"{100*KAREA[9]/core['thr9']:.0f}\\,\\%"
N["ThrNineCore"] = f"\\SI{{{core['thr9']:.0f}}}{{\\micro\\metre\\squared}}"

with open(TAB / "tab_compare.tex", "w") as f:
    f.write("\\begin{table}\n\\caption{Comparison with routed standard-cell implementations in the same PDK (TT). "
            "Standard-cell energy is the routed power at \\SI{100}{\\mega\\hertz} with input activity 0.5 divided by the "
            "clock rate; QFG energy is per operation with return-to-zero inputs (range over thresholds). Cell area is the "
            "sum of standard-cell areas; block area is the routed core of the standard-cell design or the bounding box of the "
            "QFG layout. All QFG entries are from complete DRC/LVS-clean layouts and extracted simulation.}\n"
            "\\label{tab:compare}\n\\centering\\small\\setlength{\\tabcolsep}{3.5pt}\n\\begin{tabular}{l l c r r r r}\n\\toprule\n"
            "Implementation & Functions & Config. & \\multicolumn{2}{c}{Area (\\si{\\micro\\metre\\squared})} & Delay & Energy \\\\\n"
            " & & bits & cells & block & (ps) & (fJ/op) \\\\\n\\midrule\n")
    rows = [("Fixed MAJ3 gate", "MAJ3", "0", "fixed_maj3"), ("OR3/MAJ3/AND3 select", "3", "2", "recfg3_mux"),
            ("Prog.\\ threshold gate, $K=3$", "4", "2", "thr3"), ("LUT3", "256", "8", "lut3")]
    for nm, fn, cb, k in rows:
        b = base[k]
        f.write(f"{nm} & {fn} & {cb} & {b['area']:.0f} & {core[k]:.0f} & {b['delay']:.0f} & {b['E']:.0f} \\\\\n")
    f.write(f"\\textbf{{QFG cell, $K=3$ (this work)}} & 3 & analog $V_B$ & -- & {cell_area:.0f} & {q3.tpd.max():.0f} & "
            f"{q3.E.min():.0f}--{q3.E.max():.0f} \\\\\n\\midrule\n")
    b = base["thr5"]
    f.write(f"Prog.\\ threshold gate, $K=5$ & 6 & 3 & {b['area']:.0f} & {core['thr5']:.0f} & {b['delay']:.0f} & {b['E']:.0f} \\\\\n")
    f.write(f"\\textbf{{QFG cell, $K=5$ (this work)}} & 5 & analog $V_B$ & -- & {KAREA[5]:.0f} & {KX[5]['tpd']:.0f} & "
            f"{KX[5]['Emin']:.0f}--{KX[5]['Emax']:.0f} \\\\\n\\midrule\n")
    for nm, fn, cb, k in [("Prog.\\ threshold gate, $K=9$", "10", "4", "thr9"), ("LUT7 (for scale)", "$2^{128}$", "128", "lut7")]:
        b = base[k]
        f.write(f"{nm} & {fn} & {cb} & {b['area']:.0f} & {core[k]:.0f} & {b['delay']:.0f} & {b['E']:.0f} \\\\\n")
    f.write(f"\\textbf{{QFG cell, $K=9$ (this work)}} & 9 & analog $V_B$ & -- & {KAREA[9]:.0f} & {k9['tpd']:.0f} & "
            f"{k9['Emin']:.0f}--{k9['Emax']:.0f} \\\\\n")
    f.write("\\bottomrule\n\\end{tabular}\n\\end{table}\n")

# ------------------------------------------------------------------ p-bit and network
S = pd.read_csv(D / "pbit_summary.csv", index_col=0).iloc[:, 0]
F = pd.read_csv(D / "pbit_fits.csv")
N["VnKTC"] = f"\\SI{{{float(S['vn_ktc_V'])*1e3:.2f}}}{{\\milli\\volt}}"
N["VnComp"] = f"\\SI{{{float(S['vn_comp_in_V'])*1e3:.2f}}}{{\\milli\\volt}}"
kn = float(np.sum(F.sigma_eff * F.sigma_xi) / np.sum(F.sigma_xi ** 2))
N["KnFit"] = f"{kn:.3f}"
N["VhalfOffset"] = mv(float(F.v_half.mean()) - float(S["vtrip_nom"]))
N["VstarSigma"] = f"\\SI{{{float(S['vt_mc_sigma'])*1e3:.1f}}}{{\\milli\\volt}}"
N["LagOne"] = f"{float(S['lag1']):+.3f}"
N["CIninefive"] = f"{float(S['ci95']):.3f}"
N["RunsZ"] = f"$z={float(S['runs_z']):+.2f}$"
A = pd.read_csv(D / "pnet_and.csv").set_index("model")
N["KLideal"] = f"{A.loc['ideal logistic p-bit','KL_mean']:.4f}"
N["KLgauss"] = f"{A.loc['ideal Gaussian-dither p-bit','KL_mean']:.4f}"
N["KLuntrimmed"] = f"{A.loc['QFG cell (mismatch)','KL_mean']:.4f}"
N["KLtrimmed"] = f"{A.loc['QFG cell (trimmed)','KL_mean']:.4f}"
N["ClampTrimmed"] = f"{100*A.loc['QFG cell (trimmed)','clamp_inference_mean']:.0f}\\,\\%"
M = pd.read_csv(D / "pnet_maxcut.csv")
mt = M[(M.model == "QFG cell (trimmed)") & (M.sweeps == 1000)]
N["MaxCutTwenty"] = f"{mt[mt.n==20].ratio_mean.mean():.3f}"
N["MaxCutSixtyFour"] = f"{mt[mt.n==64].ratio_mean.mean():.3f}"

with open(P / "numbers.tex", "w") as f:
    f.write("% auto-generated by sim/v2/make_paper_assets.py -- do not edit\n")
    for k, v in N.items():
        f.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
print(f"wrote {len(N)} numbers")


# ====================================================================== tables: sizing
with open(TAB / "tab_sizing.tex", "w") as f:
    f.write("\\begin{table}\n\\caption{Device sizes of the cell (SKY130 1.8-V devices; MIM = \\texttt{cap\\_mim\\_m3\\_1}).}\n"
            "\\label{tab:sizing}\n\\centering\\small\n\\begin{tabular}{l l l}\n\\toprule\nDevice & Role & Size \\\\\n\\midrule\n"
            "$M_P$ & PMOS load, gate = FG & $W/L = 16/0.15$ \\si{\\micro\\metre} (4 fingers) \\\\\n"
            "$M_{A,B,C}$ & input pull-downs & $W/L = 0.42/0.15$ \\si{\\micro\\metre} \\\\\n"
            "$M_R$ & reset switch & $W/L = 0.42/0.50$ \\si{\\micro\\metre} \\\\\n"
            "Inverter & output restore & $1.0/0.15$ (P), $0.42/0.15$ (N) \\si{\\micro\\metre} \\\\\n"
            "$C_\\mathrm{in}$ (3$\\times$) & input coupling & $2\\times2$ \\si{\\micro\\metre} (\\SI{9.5}{\\femto\\farad}) \\\\\n"
            "$C_B$ & ballast to ground & $9.2\\times2.55$ \\si{\\micro\\metre} (\\SI{51}{\\femto\\farad}) \\\\\n"
            f"FG node & total & $C_\\mathrm{{FG}}\\approx$ {N['CFG']}, $\\Delta\\approx$ {N['DeltaTT']} \\\\\n"
            "\\bottomrule\n\\end{tabular}\n\\end{table}\n")

# ====================================================================== figures
def save(fig, name):
    fig.savefig(FIG / f"{name}.pdf"); plt.close(fig); print("figure", name)

shutil.copy(ROOT / "figures/v2/tikz/fig_schematic.pdf", FIG / "fig_schematic.pdf")
shutil.copy(ROOT / "layout/v2/klayout/qfg_tlg_layout.png", FIG / "fig_layout.png")

MODE_COL = {"AND3": "0.15", "MAJ3": "0.45", "OR3": "0.7"}

def fig_windows():
    sw = pd.read_csv(D / "fig_vbsweep_tt.csv")
    fig, ax = plt.subplots(1, 2, figsize=(W2, 2.4), gridspec_kw=dict(width_ratios=[1.25, 1]))
    a = ax[0]
    ls = ["-", "--", "-.", ":", (0, (5, 1)), (0, (3, 1, 1, 1)), (0, (1, 1)), (0, (8, 2))]
    for m in range(8):
        s = sw[sw.view == "schematic"]; x = sw[sw.view == "pex"]
        a.plot(s.vb, s[f"y{m}"], ls=ls[m], color="k", lw=0.8, label=f"{m:03b}")
        a.plot(x.vb[::6], x[f"y{m}"][::6], ls="none", marker="o", ms=2, mfc="none", color="k", mew=0.4)
    w = W[(W.view == "pex") & (W.corner == "tt")].iloc[0]
    for mode, lo, hi in (("AND3", w.AND3_lo, w.AND3_hi), ("MAJ3", w.MAJ3_lo, w.MAJ3_hi), ("OR3", w.OR3_lo, 1.25)):
        a.axvspan(lo, hi, color=MODE_COL[mode], alpha=0.18, lw=0)
        a.text((lo + hi) / 2, 1.9, mode, ha="center", fontsize=7)
    a.set_xlim(-0.05, 1.25); a.set_ylim(-0.1, 2.05)
    a.set_xlabel("$V_B$ (V)"); a.set_ylabel("$Y$ (V)")
    a.legend(title="ABC", ncol=2, fontsize=6, title_fontsize=6, loc="center right", frameon=False)
    a.set_title("(a)", loc="left", fontsize=8)
    b = ax[1]
    for i, c in enumerate(order):
        for j, (mode, lo_k, hi_k) in enumerate((("AND3", "AND3_lo", "AND3_hi"), ("MAJ3", "MAJ3_lo", "MAJ3_hi"), ("OR3", "OR3_lo", "OR3_hi"))):
            xw = W[(W.view == "pex") & (W.corner == c)].iloc[0]; sw_ = W[(W.view == "schematic") & (W.corner == c)].iloc[0]
            y = i * 1.0 + (j - 1) * 0.25
            b.barh(y, xw[hi_k] - xw[lo_k], left=xw[lo_k], height=0.2, color=MODE_COL[mode], edgecolor="k", lw=0.3)
            b.barh(y, sw_[hi_k] - sw_[lo_k], left=sw_[lo_k], height=0.2, fill=False, edgecolor="k", lw=0.6, ls="--")
            vb = V[V.corner == c].iloc[0][f"vb_{mode[:-1] if mode!='MAJ3' else 'MAJ'}"] if mode != "OR3" else V[V.corner == c].iloc[0]["vb_OR"]
            b.plot(vb, y, marker="D", ms=3, color="k")
    b.set_yticks(range(5)); b.set_yticklabels([c.upper() for c in order])
    b.set_xlabel("$V_B$ (V)"); b.set_xlim(-0.05, 1.3); b.invert_yaxis()
    from matplotlib.patches import Patch
    b.legend(handles=[Patch(color=MODE_COL[m], label=m) for m in MODE_COL], fontsize=6, frameon=False, loc="lower right")
    b.set_title("(b)", loc="left", fontsize=8)
    fig.tight_layout(); save(fig, "fig_windows")

def fig_wave():
    fig, ax = plt.subplots(2, 3, figsize=(W2, 2.8), sharex=True)
    for j, (mode, vb) in enumerate((("AND3", "0.3070"), ("MAJ3", "0.5710"), ("OR3", "0.8490"))):
        a = np.loadtxt(D / f"wave_pex_{vb}.txt", skiprows=1)
        t = a[:, 0] * 1e9
        ax[0, j].plot(t, a[:, 2], "k-", lw=0.6, label="A")
        ax[0, j].plot(t, a[:, 3] + 0.0, "k--", lw=0.6, label="B")
        ax[0, j].plot(t, a[:, 4], "k:", lw=0.8, label="C")
        ax[0, j].plot(t, a[:, 5], color="0.5", lw=1.0, label="FG")
        ax[1, j].plot(t, a[:, 7], "k-", lw=0.8, label="Y")
        ax[1, j].plot(t, a[:, 6], color="0.55", lw=0.8, label="$Y_B$")
        ax[0, j].set_title(f"{mode} ($V_B$ = {float(vb):.3f} V)", fontsize=7)
        ax[1, j].set_xlabel("time (ns)")
    ax[0, 0].set_ylabel("V"); ax[1, 0].set_ylabel("V")
    ax[0, 0].legend(fontsize=5.5, ncol=2, frameon=False); ax[1, 0].legend(fontsize=6, frameon=False)
    fig.tight_layout(); save(fig, "fig_wave")

def fig_mc():
    fig, ax = plt.subplots(1, 2, figsize=(W2, 2.2))
    for n, ls in zip((1, 2, 3), ("-", "--", ":")):
        u = mc[f"vt{n}"] - n * mc.delta
        ax[0].hist(u, bins=25, histtype="step", color="k", ls=ls, label=f"$u_{n}$")
    vt = V[V.corner == "tt"].iloc[0]
    ymax = ax[0].get_ylim()[1]
    for m in ("AND", "MAJ", "OR"):
        ax[0].axvline(vt[f"vb_{m}"], color="0.5", lw=0.8, ls="-.")
        ax[0].text(vt[f"vb_{m}"] + 0.01, ymax * 1.02, f"$V_B^{{\\mathrm{{{m}}}}}$", fontsize=6, ha="center", va="bottom")
    ax[0].set_ylim(0, ymax * 1.15)
    ax[0].set_xlabel("$u_n = V_{t,n}-n\\Delta$ (V)"); ax[0].set_ylabel("count"); ax[0].legend(frameon=False, loc="center left", fontsize=6)
    ax[0].set_title("(a)", loc="left", fontsize=8)
    u1, u2, u3 = (mc[f"vt{n}"] - n * mc.delta for n in (1, 2, 3))
    marg = {"AND3": np.minimum(vt.vb_AND - u3, u2 - vt.vb_AND), "MAJ3": np.minimum(vt.vb_MAJ - u2, u1 - vt.vb_MAJ),
            "OR3": vt.vb_OR - u1}
    ax[1].boxplot([marg[k] * 1e3 for k in marg], tick_labels=list(marg), widths=0.5,
                  medianprops=dict(color="k"), boxprops=dict(color="k"), flierprops=dict(marker=".", ms=2))
    ax[1].set_ylabel("margin to window edge (mV)"); ax[1].axhline(0, color="k", lw=0.5)
    ax[1].set_title("(b)", loc="left", fontsize=8)
    fig.tight_layout(); save(fig, "fig_mc")

def fig_retention():
    fig, ax = plt.subplots(figsize=(W1, 2.3))
    for mode, mk in (("AND3", "o"), ("MAJ3", "s"), ("OR3", "^")):
        r = R[(R["mode"] == mode) & (R.n_on == 3) & (R.corner == "tt")].sort_values("temp")
        ax.semilogy(r.temp, r.t_hold_10mV_s, "k-", marker=mk, ms=3, mfc="none", label=f"{mode}, 10 mV")
        ax.semilogy(r.temp, r.t_hold_50mV_s, "k--", marker=mk, ms=3, label=f"{mode}, 50 mV")
    ff = R[(R.corner == "ff") & (R.n_on == 3)]
    ax.semilogy(ff.temp, ff.t_hold_10mV_s, ls="none", marker="x", color="0.4", ms=4, label="FF, 10 mV")
    ax.set_xlabel("temperature ($^\\circ$C)"); ax.set_ylabel("hold time (s)")
    ax.legend(fontsize=5.5, frameon=False, ncol=2)
    fig.tight_layout(); save(fig, "fig_retention")

for fn in (fig_windows, fig_wave, fig_mc, fig_retention):
    try:
        fn()
    except Exception as e:
        print("FIGURE FAILED", fn.__name__, repr(e))


def fig_kscale():
    Wd = pd.read_csv(D / "kscale_windows.csv")
    S = pd.read_csv(D / "kscale_summary.csv")
    fig, ax = plt.subplots(1, 4, figsize=(W2, 2.1))
    for _, s in S.iterrows():
        w = Wd[(Wd.K == s.K) & (Wd.swing == s.swing) & (Wd.wp == s.wp)]
        ax[0].plot(w["T"], w.width * 1e3, "k-", marker="osD^v"[int(s.K - 3) // 2 % 5], ms=2.5, lw=0.7, mfc="white",
                   alpha=0.45 + 0.55 * (s.K - 3) / 6, label=f"$K$={int(s.K)}")
    ax[0].set_xlabel("threshold $T$"); ax[0].set_ylabel("window width (mV)"); ax[0].set_title("(a)", loc="left", fontsize=8)
    ax[0].set_xticks([1, 3, 5, 7, 9]); ax[0].set_xlim(0.5, 9.5); ax[0].legend(fontsize=5.5, frameon=False, handlelength=1.5)
    Ks = [3, 5, 7, 9]; Kq = [3, 5, 9]
    thr = [base[f"thr{k}"] for k in Ks]; lut = [base.get(f"lut{k}") for k in (3, 5, 7)]
    q_area = [KAREA[k] for k in Kq]
    q_del = [float(xt.tpd.max()), KX[5]["tpd"], KX[9]["tpd"]]
    q_E = [float(xt.E.mean()), (KX[5]["Emin"] + KX[5]["Emax"]) / 2, (k9["Emin"] + k9["Emax"]) / 2]
    for a, q, st, sl, lab in ((ax[1], q_area, [core[f"thr{k}"] for k in Ks], [core[f"lut{k}"] for k in (3, 5, 7)], "block area (µm$^2$)"),
                              (ax[2], q_del, [t["delay"] for t in thr], [l["delay"] for l in lut], "delay (ps)"),
                              (ax[3], q_E, [t["E"] for t in thr], [l["E"] for l in lut], "energy (fJ/op)")):
        a.semilogy(Kq, q, "k-o", ms=3, label="QFG cell (layout, extracted)")
        a.semilogy(Ks, st, "k--s", ms=3, mfc="none", label="std-cell thr.")
        a.semilogy([3, 5, 7], sl, "k:^", ms=3, mfc="none", label="std-cell LUT")
        a.set_xlabel("fan-in $K$"); a.set_ylabel(lab); a.set_xticks(Ks)
        a.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    h, l = ax[1].get_legend_handles_labels()
    fig.legend(h, l, loc="upper center", bbox_to_anchor=(0.62, 1.0), ncol=3, fontsize=6, frameon=False)
    for a, t in zip(ax[1:], "bcd"):
        a.set_title(f"({t})", loc="left", fontsize=8)
    fig.tight_layout(rect=(0, 0, 1, 0.9)); save(fig, "fig_kscale")


def fig_pbit():
    Sg = pd.read_csv(D / "pbit_sigmoid.csv"); Fi = pd.read_csv(D / "pbit_fits.csv"); Ac = pd.read_csv(D / "pbit_autocorr.csv")
    from scipy.stats import norm
    fig, ax = plt.subplots(1, 3, figsize=(W2, 2.0))
    mk = ["o", "s", "^", "D"]
    for (s, g), m, (_, f_) in zip(Sg.groupby("sigma_xi"), mk, Fi.iterrows()):
        x = (g.vb - f_.v_half) * 1e3
        ax[0].plot(x, g.p1, ls="none", marker=m, ms=3, mfc="none", color="k", label=f"{s*1e3:.0f} mV")
        xx = np.linspace(x.min(), x.max(), 100)
        ax[0].plot(xx, norm.cdf(xx / (f_.sigma_eff * 1e3)), "k-", lw=0.6)
    ax[0].set_xlabel("$V_B - V_{1/2}$ (mV)"); ax[0].set_ylabel("$P(m=1)$"); ax[0].legend(title="$\\sigma_\\xi$", fontsize=5.5, title_fontsize=6, frameon=False)
    ax[1].plot(Fi.sigma_xi * 1e3, Fi.sigma_eff * 1e3, "ko", ms=3)
    xx = np.linspace(0, Fi.sigma_xi.max() * 1e3, 10)
    ax[1].plot(xx, kn * xx, "k--", lw=0.7, label=f"slope {kn:.3f}")
    ax[1].set_xlabel("dither $\\sigma_\\xi$ (mV)"); ax[1].set_ylabel("$\\sigma_\\mathrm{eff}$ on FG (mV)"); ax[1].legend(fontsize=6, frameon=False)
    ci = float(S["ci95"])
    ax[2].bar(Ac.lag, Ac.ac, color="0.5", width=0.6); ax[2].axhline(ci, color="k", ls="--", lw=0.6); ax[2].axhline(-ci, color="k", ls="--", lw=0.6)
    ax[2].set_xlabel("lag"); ax[2].set_ylabel("autocorrelation")
    for a, t in zip(ax, "abc"):
        a.set_title(f"({t})", loc="left", fontsize=8)
    fig.tight_layout(); save(fig, "fig_pbit")


def fig_pnet():
    Dd = pd.read_csv(D / "pnet_and_dist.csv").set_index("model")
    fig, ax = plt.subplots(1, 2, figsize=(W2, 2.1))
    states = [c for c in Dd.columns]
    xs = np.arange(len(states)); wdt = 0.2
    styles = {"Boltzmann": dict(color="k"), "ideal logistic p-bit": dict(color="0.4"),
              "QFG cell (mismatch)": dict(color="w", edgecolor="k", hatch="////"), "QFG cell (trimmed)": dict(color="0.8", edgecolor="k")}
    for i, (mdl, st) in enumerate(styles.items()):
        if mdl in Dd.index:
            ax[0].bar(xs + (i - 1.5) * wdt, Dd.loc[mdl, states], width=wdt, lw=0.3, label=mdl, **st)
    ax[0].set_xticks(xs); ax[0].set_xticklabels([s for s in states], fontsize=6)
    ax[0].set_xlabel("state (A B C)"); ax[0].set_ylabel("probability"); ax[0].set_ylim(0, 0.42)
    ax[0].legend(fontsize=5.5, frameon=False, loc="upper center", ncol=2)
    agg = M[M.sweeps == 1000].groupby(["n", "graph", "model"]).ratio_mean.mean().unstack()
    agg = agg[[c for c in ("ideal", "QFG cell (trimmed)", "QFG cell (mismatch)") if c in agg.columns]]
    lab = [f"{g}\nn={n}" for n, g in agg.index]
    xs = np.arange(len(agg))
    for i, (c, st) in enumerate(zip(agg.columns, (dict(color="0.4"), dict(color="0.8", edgecolor="k"), dict(color="w", edgecolor="k", hatch="////")))):
        ax[1].bar(xs + (i - 1) * 0.25, agg[c], width=0.25, lw=0.3, label=c, **st)
    ax[1].set_xticks(xs); ax[1].set_xticklabels(lab, fontsize=6); ax[1].set_ylim(0.95, 1.008)
    ax[1].set_ylabel("approximation ratio (1000 sweeps)"); ax[1].legend(fontsize=5.5, frameon=False, loc="lower center", ncol=3)
    for a, t in zip(ax, "ab"):
        a.set_title(f"({t})", loc="left", fontsize=8)
    fig.tight_layout(); save(fig, "fig_pnet")


for fn in (fig_kscale, fig_pbit, fig_pnet):
    try:
        fn()
    except Exception as e:
        print("FIGURE FAILED", fn.__name__, repr(e))

# p-bit area estimate with 8 unit-weight neighbours (+1 noise cap): K=3 layout + 6 extra cap tiles + 1 enable pull-down
_pb8 = cell_area + (9 - 3) * 3.6 * 4.35
N["PbitAreaEight"] = f"\\SI{{{_pb8:.0f}}}{{\\micro\\metre\\squared}}"
with open(P / "numbers.tex", "w") as f:
    f.write("% auto-generated by sim/v2/make_paper_assets.py -- do not edit\n")
    for k, v in N.items():
        f.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
print(f"rewrote numbers.tex with {len(N)} entries")


# ====================================================================== round-2 experiments
RB = pd.read_csv(D / "robust.csv", dtype={"truth": str})
N["RobustOK"] = f"{int(RB.ok.sum())}/{len(RB)}"
lab = {"vdd": ("Supply $V_\\mathrm{DD}$", "V"), "temp": ("Temperature", "\\si{\\celsius}"),
       "edge": ("Input edge time", "ps"), "load": ("Output load", "fF"), "reset": ("Reset width", "ns")}
with open(TAB / "tab_robust.tex", "w") as f:
    f.write("\\begin{table}\n\\caption{Robustness of the extracted cell at the TT process corner (one parameter varied at a time; "
            "otherwise \\SI{27}{\\celsius}, \\SI{1.80}{\\volt}, \\SI{50}{\\pico\\second} edges, \\SI{5}{\\femto\\farad}, "
            "\\SI{1}{\\nano\\second} reset, \\SI{0.3}{\\nano\\second} RZ pulses). For supply and temperature, $V_B$ is re-derived "
            "by the replica. Correct = all three modes give correct truth tables.}\n\\label{tab:robust}\n\\centering\\small\n"
            "\\begin{tabular}{l l c r r}\n\\toprule\nParameter & Value & Correct & $t_\\mathrm{pd,max}$ (ps) & $E$ (fJ/op) \\\\\n\\midrule\n")
    for kind in ("vdd", "temp", "edge", "load", "reset"):
        g = RB[RB.kind == kind]
        for j, (v, gg) in enumerate(g.groupby("value", sort=True)):
            nm, un = lab[kind]
            vv = f"{v:.2f}" if kind == "vdd" else (f"{v:.1f}" if kind == "reset" else f"{v:.0f}")
            f.write(f"{nm if j==0 else ''} & {vv} {un} & {'yes' if gg.ok.all() else 'no'} & {gg.tpd_ps.max():.0f} & "
                    f"{gg.E_fJ.min():.0f}--{gg.E_fJ.max():.0f} \\\\\n")
        f.write("\\addlinespace\n" if kind != "reset" else "")
    f.write("\\bottomrule\n\\end{tabular}\n\\end{table}\n")

FW = pd.read_csv(D / "fa_window.csv"); FT = pd.read_csv(D / "fa_timing.csv")
FS = pd.read_csv(D / "fa_ss_tp.csv") if (D / "fa_ss_tp.csv").exists() else None
with open(TAB / "tab_fa.tex", "w") as f:
    f.write("\\begin{table}\n\\caption{Cascaded threshold-logic full adder (schematic, \\SI{0.6}{\\nano\\second} RZ pulses): "
            "window of $V_{B2}$ in which carry and sum are correct for all eight inputs, and settling time and energy at the "
            "window centre. Settling times are worst-case over the eight inputs and include the sum glitch for inputs that "
            "produce a carry (the sum rises before $\\overline{C_\\mathrm{out}}$ falls).}\n\\label{tab:fa}\n\\centering\\small\n\\begin{tabular}{l c c r r r}\n\\toprule\n"
            "Corner & $V_{B2}$ window (V) & Correct & $t_\\mathrm{s}$ carry (ps) & $t_\\mathrm{s}$ sum (ps) & $E$ (fJ/add) \\\\\n\\midrule\n")
    for c in order:
        g = FW[(FW.corner == c) & FW.ok]; t = FT[FT.corner == c].iloc[0]
        f.write(f"{c.upper()} & {g.vb2.min():.2f}--{g.vb2.max():.2f} & {'yes' if t.ok else 'no'} & {t.tpd_cout_ps:.0f} & "
                f"{t.tpd_sum_ps:.0f} & {t.E_fJ_per_add:.0f} \\\\\n")
    f.write("\\bottomrule\n\\end{tabular}\n\\end{table}\n")
fw_tt = FW[(FW.corner == "tt") & FW.ok]; fw_ss = FW[(FW.corner == "ss") & FW.ok]
N["FAwinTT"] = mv(fw_tt.vb2.max() - fw_tt.vb2.min()); N["FAwinSS"] = mv(fw_ss.vb2.max() - fw_ss.vb2.min())
N["FAtpdTT"] = ps(float(FT[FT.corner == "tt"].tpd_sum_ps.iloc[0]))
N["FAtpdSS"] = ps(float(FT[FT.corner == "ss"].tpd_sum_ps.iloc[0]))
N["FAenergyTT"] = f"\\SI{{{float(FT[FT.corner=='tt'].E_fJ_per_add.iloc[0])/1000:.1f}}}{{\\pico\\joule}}"
if FS is not None:
    g = FS[(FS.t_p == FS.t_p.max()) & FS.ok]
    N["FAwinSSlong"] = mv(g.vb2.max() - g.vb2.min()); N["FAtpLong"] = f"\\SI{{{FS.t_p.max():.1f}}}{{\\nano\\second}}"

CY = pd.read_csv(D / "calib_yield.csv")
with open(TAB / "tab_calib.tex", "w") as f:
    f.write("\\begin{table}\n\\caption{Replica-cell self-calibration with mismatch (100 samples per corner). Model agreement: "
            "window model against transient truth tables at the nominal $V_B$. Pair yield: fraction of (replica, cell) pairs "
            "for which all three modes are correct when $V_B$ is set from the replica through a DAC and a buffer with the "
            "given offset.}\n\\label{tab:calib}\n\\centering\\small\n\\begin{tabular}{l c c c c c}\n\\toprule\n"
            "Corner & Transient yield & Model & \\multicolumn{3}{c}{Pair yield (DAC bits / buffer $\\sigma$)} \\\\\n"
            " & at nominal $V_B$ & agreement & 6 / 0 mV & 8 / 3 mV & 6 / 5 mV \\\\\n\\midrule\n")
    for c in order:
        g = CY[CY.corner == c]
        py = lambda b, s_: float(g[(g.bits == b) & (g.buffer_sigma_mV == s_)].pair_yield.iloc[0])
        f.write(f"{c.upper()} & {100*g.transient_yield_nominal.iloc[0]:.0f}\\,\\% & {100*g.model_agreement.iloc[0]:.4g}\\,\\% & "
                f"{100*py(6,0):.4g}\\,\\% & {100*py(8,3):.4g}\\,\\% & {100*py(6,5):.4g}\\,\\% \\\\\n")
    f.write("\\bottomrule\n\\end{tabular}\n\\end{table}\n")
N["CalibMinYield"] = f"{100*CY.pair_yield.min():.4g}\\,\\%"
N["CalibMinAgree"] = f"{100*CY.model_agreement.min():.0f}\\,\\%"

shutil.copy(ROOT / "layout/v2k/K9/klayout/qfg_tlg_k9_layout.png", FIG / "fig_layout_k9.png")


def fig_fa():
    a = np.loadtxt(D / "fa_wave_tt.txt")
    t = a[:, 0] * 1e9
    fig, ax = plt.subplots(3, 1, figsize=(W2, 2.9), sharex=True)
    ax[0].plot(t, a[:, 1], "k-", lw=0.6, label="A"); ax[0].plot(t, a[:, 2], "k--", lw=0.6, label="B")
    ax[0].plot(t, a[:, 3], "k:", lw=0.8, label="C"); ax[0].legend(fontsize=6, frameon=False, loc="upper left", bbox_to_anchor=(1.0, 1.0))
    ax[1].plot(t, a[:, 4], color="0.5", lw=0.8, label="$\\overline{C_\\mathrm{out}}$"); ax[1].plot(t, a[:, 5], "k-", lw=0.8, label="FG$_2$")
    ax[1].legend(fontsize=6, frameon=False, loc="upper left", bbox_to_anchor=(1.0, 1.0))
    ax[2].plot(t, a[:, 6], color="0.5", lw=0.9, label="$C_\\mathrm{out}$"); ax[2].plot(t, a[:, 7], "k-", lw=0.9, label="Sum")
    ax[2].legend(fontsize=6, frameon=False, loc="upper left", bbox_to_anchor=(1.0, 1.0)); ax[2].set_xlabel("time (ns)")
    for k, lbl in enumerate(["000", "001", "010", "011", "100", "101", "110", "111"]):
        ax[0].text(k * 4 + 2.2, 2.0, lbl, fontsize=6, ha="center", va="bottom")
    for x in ax:
        x.set_ylabel("V"); x.set_ylim(-0.1, 2.0 if x is not ax[0] else 2.35)
    fig.tight_layout(); save(fig, "fig_fa")


for fn in (fig_fa, fig_kscale):
    try:
        fn()
    except Exception as e:
        print("FIGURE FAILED", fn.__name__, repr(e))
with open(P / "numbers.tex", "w") as f:
    f.write("% auto-generated by sim/v2/make_paper_assets.py -- do not edit\n")
    for k, v in N.items():
        f.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
print(f"rewrote numbers.tex with {len(N)} entries (round 2)")
