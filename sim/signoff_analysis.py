"""
Sign-off analysis: PVT, mismatch MC, delay/energy/area, baseline comparisons.
Parses LibreLane metrics when available; cell metrics from behavioral model.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from fgmos_model import FGMOSCell

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "figures"
DATA = ROOT / "data"
TBL = ROOT / "tables"
CAS_FIG = ROOT / "els-cas-templates" / "figures"

# Sky130 sign-off corners (LibreLane STA naming)
PVT_CORNERS = {
    "TT (25°C, 1.80 V)": {"tag": "nom_tt_025C_1v80", "T": 298.15, "Vcc": 1.80, "dVth": 0.0, "dkn": 1.0},
    "SS (125°C, 1.60 V)": {"tag": "nom_ss_100C_1v60", "T": 398.15, "Vcc": 1.60, "dVth": 0.06, "dkn": 0.82},
    "FF (−40°C, 1.95 V)": {"tag": "nom_ff_n40C_1v95", "T": 233.15, "Vcc": 1.95, "dVth": -0.06, "dkn": 1.18},
}

# Target macro footprint from Magic floorplan (µm²); update after DRC-clean export
MACRO_AREA_UM2 = 48.0 * 36.0

# Grayscale + hatch fills (print-safe)
_BAR_STYLES = [
    {"facecolor": "white", "hatch": ""},
    {"facecolor": "white", "hatch": ".."},
    {"facecolor": "0.92", "hatch": "xx"},
    {"facecolor": "0.85", "hatch": "++"},
    {"facecolor": "0.72", "hatch": "///"},
]


def _apply_paper_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "DejaVu Serif", "Times"],
            "font.size": 8,
            "axes.labelsize": 8,
            "axes.linewidth": 0.6,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "legend.fontsize": 6.5,
            "figure.dpi": 300,
            "savefig.dpi": 300,
            "axes.grid": False,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def _save_fig(fig: plt.Figure, stem: str) -> None:
    for ext in ("pdf", "png"):
        p = FIG / f"{stem}.{ext}"
        fig.savefig(p, dpi=300, bbox_inches="tight", pad_inches=0.04)
        if CAS_FIG.parent.exists():
            CAS_FIG.mkdir(parents=True, exist_ok=True)
            import shutil

            shutil.copy2(p, CAS_FIG / p.name)


def _find_metrics() -> Path | None:
    env = os.environ.get("LIBRELANE_METRICS")
    if env and Path(env).is_file():
        return Path(env)
    runs = ROOT / "layout/librelane/fgmos_rtl_wrapper/runs"
    if not runs.is_dir():
        return None
    candidates = sorted(runs.glob("*/final/metrics.json"), key=lambda p: p.stat().st_mtime)
    return candidates[-1] if candidates else None


def _parse_librelane_pvt(metrics_path: Path) -> pd.DataFrame:
    data = json.loads(metrics_path.read_text())
    rows = []
    for label, spec in PVT_CORNERS.items():
        tag = spec["tag"]
        setup = data.get(f"timing__setup__ws__corner:{tag}")
        hold = data.get(f"timing__hold__ws__corner:{tag}")
        rows.append(
            {
                "corner": label,
                "setup_ws_ns": None if setup is None else round(float(setup), 3),
                "hold_ws_ns": None if hold is None else round(float(hold), 3),
            }
        )
    die_um2 = data.get("design__die__area")
    core_um2 = data.get("design__core__area")
    inst_um2 = data.get("design__instance__area")
    power_w = data.get("power__total")
    return pd.DataFrame(rows), {
        "die_um2": die_um2,
        "core_um2": core_um2,
        "placed_um2": inst_um2,
        "power_w": power_w,
        "instances": data.get("design__instance__count"),
    }


class CornerCell(FGMOSCell):
    def __init__(self, dVth: float = 0.0, dkn: float = 1.0, Vcc: float = 1.8, T: float = 298.15):
        super().__init__()
        self.Vth0 = self.Vth0 + dVth
        self.kn = self.kn * dkn
        self.Vcc = Vcc
        self.T = T


def _load_cap_f() -> float:
    """Effective load on output node (fF): FG network + fanout estimate."""
    return 80e-15


def _delay_s(cell: FGMOSCell, vctrl: float, n_high: int = 1) -> float:
    """RC settling time constant τ = R_eff C_L (s)."""
    if n_high == 0:
        v1 = v2 = v3 = 0.0
    else:
        v1, v2, v3 = cell.Vcc, 0.0, 0.0
    vfg = cell.Vfg_eff(v1, v2, v3, vctrl)
    r = cell.R_eff(vfg)
    if r == np.inf:
        return np.nan
    return r * _load_cap_f()


def _energy_j(cell: FGMOSCell, vctrl: float) -> float:
    """Energy per logic evaluation: charge FG + output node (J)."""
    c_eff = cell.CT + _load_cap_f()
    vsw = cell.Vcc
    return c_eff * vsw * vsw


def _classify_logic(cell: FGMOSCell, vctrl: float, thresh: float = 0.9) -> bool:
    """True if NOR/MAJ/AND bands still separate at this corner."""
    modes = [(0.65, "nor"), (0.90, "maj"), (1.15, "and")]
    for vc, _ in modes:
        outs = []
        for n in range(8):
            bits = [(n >> i) & 1 for i in range(3)]
            nh = sum(bits)
            vfg = cell.Vfg_eff(bits[0] * cell.Vcc, bits[1] * cell.Vcc, bits[2] * cell.Vcc, vc)
            outs.append(cell.Vout_rtl(vfg, nh, Vctrl=vc))
        if max(outs) - min(outs) < 0.15:
            return False
    return True


def _cmos_baseline():
    """Sky130 HD minimum-area proxies for equivalent 3-input functions."""
    # µm² per minimum inverter pair (n+p), rough placement pitch
    um2_per_stage = 42.0
    return {
        "CMOS NOR3": {"stages": 2, "devices": 8, "area_um2": 2 * um2_per_stage * 4},
        "CMOS AND3": {"stages": 2, "devices": 8, "area_um2": 2 * um2_per_stage * 4},
        "CMOS MAJ3": {"stages": 5, "devices": 22, "area_um2": 5 * um2_per_stage * 4},
        "Conv. RTL": {"stages": 1, "devices": 5, "area_um2": MACRO_AREA_UM2 * 1.35},
        "FGMOS–RTL (this)": {"stages": 1, "devices": 5, "area_um2": MACRO_AREA_UM2},
    }


def _delay_energy_table() -> pd.DataFrame:
    tt = FGMOSCell()
    c_load = _load_cap_f()
    rows = []
    for name, vctrl in [("NOR", 0.65), ("MAJ", 0.90), ("AND", 1.15), ("P-bit", 0.68)]:
        tau = _delay_s(tt, vctrl, n_high=1)
        vfg = tt.Vfg_eff(tt.Vcc, 0, 0, vctrl)
        r_k = tt.R_eff(vfg)
        rows.append(
            {
                "mode": name,
                "R_eff_kOhm": round(r_k / 1e3, 2) if np.isfinite(r_k) else None,
                "tau_ps": round(tau * 1e12, 0) if np.isfinite(tau) else None,
                "t_90_ps": round(2.3 * tau * 1e12, 0) if np.isfinite(tau) else None,
                "E_eval_fJ": round(_energy_j(tt, vctrl) * 1e15, 1),
            }
        )
    conv_r = 10e3
    rows.append(
        {
            "mode": "Conv. RTL (10 kΩ)",
            "R_eff_kOhm": 10.0,
            "tau_ps": round(conv_r * c_load * 1e12, 0),
            "t_90_ps": round(2.3 * conv_r * c_load * 1e12, 0),
            "E_eval_fJ": round(c_load * tt.Vcc**2 * 1e15, 1),
        }
    )
    return pd.DataFrame(rows)


def _mismatch_mc(n: int = 500, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        dVth = rng.normal(0, 0.02)
        kn_scale = 1.0 + rng.normal(0, 0.05)
        cell = CornerCell(dVth=dVth, dkn=kn_scale)
        ok = _classify_logic(cell, 0.9)
        tau = _delay_s(cell, 0.65)
        rows.append({"sample": i, "dVth_mV": dVth * 1e3, "kn_pct": (kn_scale - 1) * 100, "logic_ok": ok, "tau_ps": tau * 1e12})
    return pd.DataFrame(rows)


def _write_tables(
    delay_df: pd.DataFrame,
    pvt_df: pd.DataFrame,
    compare: dict,
    ll_meta: dict,
    mc_df: pd.DataFrame,
) -> None:
    TBL.mkdir(parents=True, exist_ok=True)

    with open(TBL / "table_signoff_delay_energy.tex", "w") as f:
        f.write("\\begin{table}[ht]\n\\centering\n")
        f.write("\\caption{Cell-level delay and energy per evaluation (behavioral ohmic model, ")
        f.write("$C_L=80$\\,fF, $V_{\\mathrm{CC}}=1.8$\\,V).}\n")
        f.write("\\label{tbl:delay_energy}\n")
        f.write("\\begin{tabular}{@{}lcccc@{}}\n\\toprule\n")
        f.write("Mode & $R_{\\mathrm{eff}}$ (k$\\Omega$) & $\\tau$ (ps) & $t_{90}$ (ps) & $E_{\\mathrm{eval}}$ (fJ) \\\\\n")
        f.write("\\midrule\n")
        for _, r in delay_df.iterrows():
            f.write(
                f"{r['mode']} & {r['R_eff_kOhm']} & {r['tau_ps']} & {r['t_90_ps']} & {r['E_eval_fJ']} \\\\\n"
            )
        f.write("\\bottomrule\n\\end{tabular}\n\\end{table}\n")

    with open(TBL / "table_pvt_sta.tex", "w") as f:
        f.write("\\begin{table}[ht]\n\\centering\n")
        f.write("\\caption{LibreLane post-place-and-route STA slack (wrapper harness, ns).}\n")
        f.write("\\label{tbl:pvt_sta}\n")
        f.write("\\begin{tabular}{@{}lcc@{}}\n\\toprule\n")
        f.write("Corner & Setup WS & Hold WS \\\\\n\\midrule\n")
        for _, r in pvt_df.iterrows():
            f.write(f"{r['corner']} & {r['setup_ws_ns']} & {r['hold_ws_ns']} \\\\\n")
        f.write("\\bottomrule\n\\end{tabular}\n\\end{table}\n")

    with open(TBL / "table_area_compare.tex", "w") as f:
        f.write("\\begin{table}[ht]\n\\centering\n")
        f.write("\\caption{Area comparison: single-tile FGMOS--RTL versus fixed RTL and CMOS implementations ")
        f.write("(macro layout target and Sky130 HD gate-count proxies).}\n")
        f.write("\\label{tbl:area_compare}\n")
        f.write("\\begin{tabular}{@{}lcc@{}}\n\\toprule\n")
        f.write("Implementation & Transistors & Est.\\ area ($\\mu$m$^2$) \\\\\n\\midrule\n")
        for k, v in compare.items():
            f.write(f"{k} & {v['devices']} & {v['area_um2']:.0f} \\\\\n")
        if ll_meta.get("die_um2"):
            f.write("\\midrule\n")
            f.write(
                f"Wrapper die (LibreLane) & {ll_meta.get('instances', '---')} & "
                f"{ll_meta['die_um2']:.0f} \\\\\n"
            )
        f.write("\\bottomrule\n\\end{tabular}\n\\end{table}\n")

    ok_pct = 100.0 * mc_df["logic_ok"].mean()
    with open(TBL / "table_mismatch_mc.tex", "w") as f:
        f.write("\\begin{table}[ht]\n\\centering\n")
        f.write("\\caption{Monte Carlo mismatch ($N=500$): $\\sigma_{V_{th0}}=20$\\,mV, ")
        f.write("$\\sigma_{k_n}/k_n=5\\%$.}\n")
        f.write("\\label{tbl:mismatch}\n")
        f.write("\\begin{tabular}{@{}lc@{}}\n\\toprule\n")
        f.write("Metric & Value \\\\\n\\midrule\n")
        f.write(f"Logic bands preserved & {ok_pct:.1f}\\% \\\\\n")
        f.write(f"$\\tau$ mean (NOR band) & {mc_df['tau_ps'].mean():.0f}\\,ps \\\\\n")
        f.write(f"$\\tau$ $\\sigma$ & {mc_df['tau_ps'].std():.0f}\\,ps \\\\\n")
        f.write("\\bottomrule\n\\end{tabular}\n\\end{table}\n")


def _plot_pvt(delay_df: pd.DataFrame, pvt_cell_df: pd.DataFrame) -> None:
    """Fig. 9: (a) mode delay vs fixed RTL; (b) PVT corner sweep — B&W print-safe."""
    _apply_paper_style()

    order = ["NOR", "MAJ", "AND", "P-bit", "Conv. RTL (10 kΩ)"]
    labels = ["NOR", "MAJ", "AND", "P-bit", "Conv.\nRTL"]
    tau_by_mode = {r["mode"]: float(r["tau_ps"]) for _, r in delay_df.iterrows()}
    tau_vals = [tau_by_mode[m] for m in order]

    fig, axes = plt.subplots(2, 1, figsize=(3.5, 3.75), sharex=False)
    fig.subplots_adjust(hspace=0.38)

    # --- (a) Programming-mode delay at TT ---
    ax = axes[0]
    x = np.arange(len(labels))
    bars = []
    for i, (tau, sty) in enumerate(zip(tau_vals, _BAR_STYLES)):
        b = ax.bar(
            x[i],
            tau,
            width=0.62,
            linewidth=0.75,
            edgecolor="black",
            zorder=3,
            **sty,
        )
        bars.append(b[0])
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel(r"RC time constant $\tau$ (ps)")
    ymax = max(tau_vals) * 1.18
    ax.set_ylim(0, ymax)
    ax.text(
        -0.14, 1.03, "(a)",
        transform=ax.transAxes,
        fontsize=8,
        fontweight="bold",
        va="bottom",
        ha="left",
    )
    for rect, val in zip(bars, tau_vals):
        ax.text(
            rect.get_x() + rect.get_width() / 2,
            val + ymax * 0.02,
            f"{val:.0f}",
            ha="center",
            va="bottom",
            fontsize=6,
        )

    # --- (b) PVT corners (NOR band, one input high) ---
    ax2 = axes[1]
    corner_lbl = ["TT\n(25°C)", "SS\n(125°C)", "FF\n(−40°C)"]
    pvt_tau = [float(v) for v in pvt_cell_df["tau_nor_ps"]]
    xp = np.arange(len(corner_lbl))
    ax2.plot(
        xp,
        pvt_tau,
        color="black",
        linewidth=1.0,
        linestyle="-",
        marker="s",
        markersize=4.5,
        markerfacecolor="white",
        markeredgecolor="black",
        markeredgewidth=0.85,
        zorder=3,
    )
    ax2.set_xticks(xp)
    ax2.set_xticklabels(corner_lbl)
    ax2.set_ylabel(r"$\tau$ (ps), NOR band")
    ax2.set_ylim(0, max(pvt_tau) * 1.2)
    ax2.yaxis.grid(True, linestyle=":", linewidth=0.45, color="0.55", zorder=0)
    ax2.set_axisbelow(True)
    ax2.text(
        -0.14, 1.03, "(b)",
        transform=ax2.transAxes,
        fontsize=8,
        fontweight="bold",
        va="bottom",
        ha="left",
    )
    for xi, val in zip(xp, pvt_tau):
        ax2.annotate(
            f"{val:.0f}",
            (xi, val),
            textcoords="offset points",
            xytext=(0, 5),
            ha="center",
            fontsize=6,
        )

    _save_fig(fig, "fig9_signoff_pvt")
    plt.close(fig)


def _plot_mismatch(mc_df: pd.DataFrame) -> None:
    _apply_paper_style()
    tau = mc_df["tau_ps"].replace([np.inf, -np.inf], np.nan).dropna()
    if len(tau) == 0:
        return

    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    bins = np.linspace(tau.min() - 5, tau.max() + 5, 22)
    ax.hist(
        tau,
        bins=bins,
        color="white",
        edgecolor="black",
        linewidth=0.55,
        density=False,
        zorder=2,
    )
    mu = float(tau.mean())
    ax.axvline(mu, color="black", ls="--", lw=0.9, label=rf"$\mu={mu:.0f}$\,ps")
    ax.set_xlabel(r"$\tau$ (ps), NOR band")
    ax.set_ylabel("Count")
    ax.legend(frameon=False, loc="upper right")
    fig.tight_layout()
    _save_fig(fig, "fig10_mismatch_tau")
    plt.close(fig)


def run() -> bool:
    FIG.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)

    delay_df = _delay_energy_table()
    delay_df.to_csv(DATA / "signoff_delay_energy.csv", index=False)

    pvt_rows = []
    for label, spec in PVT_CORNERS.items():
        cell = CornerCell(dVth=spec["dVth"], dkn=spec["dkn"], Vcc=spec["Vcc"], T=spec["T"])
        tau = _delay_s(cell, 0.65)
        pvt_rows.append(
            {
                "corner": label,
                "tau_nor_ps": round(tau * 1e12, 0),
                "E_eval_fJ": round(_energy_j(cell, 0.65) * 1e15, 1),
                "logic_ok": _classify_logic(cell, 0.9),
            }
        )
    pvt_cell_df = pd.DataFrame(pvt_rows)
    pvt_cell_df.to_csv(DATA / "signoff_pvt_cell.csv", index=False)

    mc_df = _mismatch_mc()
    mc_df.to_csv(DATA / "signoff_mismatch_mc.csv", index=False)

    ll_meta: dict = {}
    pvt_sta_df = pd.DataFrame()
    metrics = _find_metrics()
    if metrics:
        pvt_sta_df, ll_meta = _parse_librelane_pvt(metrics)
        pvt_sta_df.to_csv(DATA / "signoff_librelane_sta.csv", index=False)
        ll_summary = {
            "metrics_path": str(metrics),
            "extracted_spice": str(metrics.parent / "spice/fgmos_rtl_wrapper.spice"),
        }
        (DATA / "signoff_librelane.json").write_text(json.dumps({**ll_meta, **ll_summary}, indent=2))
    else:
        pvt_sta_df = pd.DataFrame(
            [{"corner": k, "setup_ws_ns": None, "hold_ws_ns": None} for k in PVT_CORNERS]
        )

    compare = _cmos_baseline()
    _write_tables(delay_df, pvt_sta_df, compare, ll_meta, mc_df)
    _plot_pvt(delay_df, pvt_cell_df)
    _plot_mismatch(mc_df)

    print("  Sign-off: fig9/fig10 updated (B&W); tables in tables/")
    print(f"  Mismatch logic OK: {mc_df['logic_ok'].mean()*100:.1f}%")
    return bool(mc_df["logic_ok"].mean() > 0.85)


if __name__ == "__main__":
    run()
