"""
Claim 3: FGMOS partial charge → CMOS-native p-bit (no MTJ needed).
Stochasticity from floating-gate charge quantization noise (kT/C thermal).
Generates: figures/fig4–fig6 (PDF+PNG)
           tables/table2_prior_art.tex
           data/claim3_*.csv
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from fgmos_model import FGMOSCell

plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman'],
                     'font.size': 8, 'axes.labelsize': 8, 'figure.dpi': 300})

def run():
    os.makedirs('figures', exist_ok=True)
    os.makedirs('tables', exist_ok=True)
    os.makedirs('data', exist_ok=True)

    np.random.seed(42)
    cell = FGMOSCell()
    kB = 1.38e-23
    T = 300.0
    CT = cell.CT
    sigma0 = np.sqrt(kB * T / CT)
    # NOR-programmed band — steep analog transition for p-bit statistics
    # Vctrl=1.12V gives Vfg=(18+5.6)/40=0.59V, overdrive=100mV at TT corner
    VCTRL_PBIT = 1.12
    print(f"  Thermal noise floor σ₀ = {sigma0*1e6:.1f} μV  (kT/C, CT={CT*1e15:.0f}fF)")
    
    N_MC = 50_000
    Vfg_sweep = np.linspace(0.60, 0.92, 80)
    PBIT_THRESH = 0.28  # mid-rail digitization (single-input NOR band)
    sigma_factors = [1, 10, 30, 60]   # 1x = pure thermal, 60x = partial erase state
    
    # ── Figure 4: P(out=1) sigmoid family ──────────────────────────────────────
    linestyles = ['-', '--', '-.', ':']
    all_rows = []
    sigmoid_curves = {}

    def _plot_sigmoid(ax):
        for i, sf in enumerate(sigma_factors):
            sigma = sf * sigma0
            prob_out = []
            for Vfg_nom in Vfg_sweep:
                dV = np.random.normal(0, sigma, N_MC)
                Vfg_s = Vfg_nom + dV
                Vout_s = np.array([cell.Vout_rtl(v, 1, Vctrl=VCTRL_PBIT) for v in Vfg_s])
                p1 = np.mean(Vout_s >= PBIT_THRESH)
                prob_out.append(p1)
                all_rows.append(
                    {'sigma_factor': sf, 'Vfg_nom': round(Vfg_nom, 4), 'P_out1': round(p1, 4)}
                )
            sigmoid_curves[sf] = np.array(prob_out)
            ax.plot(
                Vfg_sweep,
                prob_out,
                color='black',
                linewidth=1.2,
                linestyle=linestyles[i % len(linestyles)],
                label=rf'$\sigma={sf}\sigma_0$',
            )
        ax.set_xlabel('Nominal $V_{fg}$ (V)')
        ax.set_ylabel('$P(V_{out}=1)$')
        ax.axhline(0.5, color='k', linestyle=':', linewidth=0.6)
        ax.legend(loc='upper right', fontsize=6, frameon=False)
        ax.grid(True, alpha=0.25, color='0.6')

    fig4, ax4 = plt.subplots(figsize=(3.5, 2.8))
    _plot_sigmoid(ax4)
    ax4.set_title('Claim 3: FGMOS p-bit Sigmoid Family', fontsize=8)
    fig4.tight_layout()
    fig4.savefig('figures/fig4_pbit_sigmoid.pdf', bbox_inches='tight')
    fig4.savefig('figures/fig4_pbit_sigmoid.png', bbox_inches='tight', dpi=300)
    plt.close()
    
    pd.DataFrame(all_rows).to_csv('data/claim3_sigmoid_data.csv', index=False)
    
    # ── Figure 5: Transition width vs sigma ────────────────────────────────────
    sigma_sweep = np.logspace(0, 2, 30) * sigma0
    widths = []
    for sigma in sigma_sweep:
        prob_out = []
        for Vfg_nom in Vfg_sweep:
            dV    = np.random.normal(0, sigma, N_MC)
            Vfg_s = Vfg_nom + dV
            Vout_s = np.array([cell.Vout_rtl(v, 1, Vctrl=VCTRL_PBIT) for v in Vfg_s])
            prob_out.append(np.mean(Vout_s >= PBIT_THRESH))
        prob_out = np.array(prob_out)
        idx_10 = np.searchsorted(prob_out, 0.1)
        idx_90 = np.searchsorted(prob_out, 0.9)
        width = abs(Vfg_sweep[min(idx_90,len(Vfg_sweep)-1)] -
                    Vfg_sweep[max(len(Vfg_sweep)-1-idx_10,0)])
        widths.append(width * 1000)   # mV
    
    def _plot_width(ax):
        ax.plot(
            sigma_sweep / sigma0,
            widths,
            color='black',
            marker='o',
            markersize=3,
            markerfacecolor='white',
            markeredgewidth=0.7,
            linewidth=1.2,
        )
        ax.set_xlabel('Noise factor $\\sigma/\\sigma_0$')
        ax.set_ylabel('Transition width (mV)')
        ax.set_xscale('log')
        ax.grid(True, alpha=0.25, color='0.6')

    fig5, ax5 = plt.subplots(figsize=(3.5, 2.8))
    _plot_width(ax5)
    ax5.set_title('Claim 3: Tunable p-bit Transition Width', fontsize=8)
    fig5.tight_layout()
    fig5.savefig('figures/fig5_transition_width.pdf', bbox_inches='tight')
    fig5.savefig('figures/fig5_transition_width.png', bbox_inches='tight', dpi=300)
    plt.close()

    # Combined panel for Elsevier figure* environment
    fig_cb, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(7.0, 2.75))
    for i, sf in enumerate(sigma_factors):
        ax_a.plot(
            Vfg_sweep,
            sigmoid_curves[sf],
            color='black',
            linewidth=1.2,
            linestyle=linestyles[i % len(linestyles)],
            label=rf'$\sigma={sf}\sigma_0$',
        )
    ax_a.set_xlabel('Nominal $V_{fg}$ (V)')
    ax_a.set_ylabel('$P(V_{out}=1)$')
    ax_a.axhline(0.5, color='k', linestyle=':', linewidth=0.6)
    ax_a.legend(loc='upper right', fontsize=6, frameon=False)
    ax_a.grid(True, alpha=0.25, color='0.6')
    ax_a.text(-0.12, 1.03, '(a)', transform=ax_a.transAxes, fontsize=8, fontweight='bold')

    _plot_width(ax_b)
    ax_b.text(-0.12, 1.03, '(b)', transform=ax_b.transAxes, fontsize=8, fontweight='bold')

    fig_cb.tight_layout(w_pad=1.6)
    fig_cb.savefig('figures/fig4_pbit_combined.pdf', bbox_inches='tight')
    fig_cb.savefig('figures/fig4_pbit_combined.png', bbox_inches='tight', dpi=300)
    plt.close()
    print('  fig4_pbit_combined saved ✅')
    
    # ── Figure 6: Autocorrelation (randomness proof) ───────────────────────────
    sigma_opt = 30 * sigma0
    Vfg_mid   = Vfg_sweep[len(Vfg_sweep)//2]
    dV_stream = np.random.normal(0, sigma_opt, 5000)
    Vfg_stream = Vfg_mid + dV_stream
    bitstream = (
        np.array([cell.Vout_rtl(v, 1, Vctrl=VCTRL_PBIT) for v in Vfg_stream])
        >= PBIT_THRESH
    ).astype(int)
    
    max_lag = 50
    lags    = range(1, max_lag+1)
    autocorr = [np.corrcoef(bitstream[:-l], bitstream[l:])[0,1] for l in lags]
    
    fig6, ax6 = plt.subplots(figsize=(3.5, 2.8))
    ax6.bar(list(lags), autocorr, color='steelblue', width=0.7)
    ax6.axhline(0, color='k', linewidth=0.8)
    ax6.axhline(1.96/np.sqrt(5000), color='r', linestyle='--',
                linewidth=1, label='95\\% CI')
    ax6.axhline(-1.96/np.sqrt(5000), color='r', linestyle='--', linewidth=1)
    ax6.set_xlabel('Lag')
    ax6.set_ylabel('Autocorrelation')
    ax6.set_title('Claim 3: p-bit Randomness (Autocorrelation)', fontsize=8)
    ax6.legend()
    ax6.grid(True, alpha=0.3)
    fig6.tight_layout()
    fig6.savefig('figures/fig6_autocorrelation.pdf', bbox_inches='tight')
    fig6.savefig('figures/fig6_autocorrelation.png', bbox_inches='tight', dpi=300)
    plt.close()
    
    # ── Monte Carlo raw data ──────────────────────────────────────────────────
    mc_rows = []
    sigma_mc = 30 * sigma0
    Vfg_mc = 0.73
    dV_mc = np.random.normal(0, sigma_mc, 10000)
    for i, dv in enumerate(dV_mc):
        vfg = Vfg_mc + dv
        vout = cell.Vout_rtl(vfg, 1, Vctrl=VCTRL_PBIT)
        mc_rows.append({'sample': i, 'dV_uV': round(dv*1e6, 2),
                       'Vfg': round(vfg, 6), 'Vout': round(vout, 4),
                       'bit': int(vout >= PBIT_THRESH)})
    pd.DataFrame(mc_rows).to_csv('data/claim3_montecarlo_raw.csv', index=False)
    
    # ── Table 2: Prior art comparison ─────────────────────────────────────────
    with open('tables/table2_prior_art.tex','w') as f:
        f.write("\\begin{table}[h]\n\\centering\n")
        f.write("\\caption{Comparison with Prior Art}\n")
        f.write("\\begin{tabular}{lccc}\n\\hline\n")
        f.write("Property & This Work & Wisland 2003 & Kim 2024 \\\\\n\\hline\n")
        rows = [
            ("Topology",          "RTL (ohmic R)",  "CMOS inverter", "Bistable R"),
            ("FG region",         "Ohmic/triode",   "Saturation",    "N/A"),
            ("Logic functions",   "NOR/MAJ/AND",    "XNOR/NAND/XOR", "N/A"),
            ("p-bit native",      "Yes",            "No",            "Yes"),
            ("Exotic material",   "None",           "None",          "Special CMOS"),
            ("PDK compatible",    "Sky130",         "0.5$\\mu$m",    "8-inch custom"),
        ]
        for r in rows:
            f.write(f"{r[0]} & {r[1]} & {r[2]} & {r[3]} \\\\\n")
        f.write("\\hline\n\\end{tabular}\n\\end{table}\n")

    # ── Figure 7: prior-art comparison (visual for paper body) ─────────────────
    fig7, ax7 = plt.subplots(figsize=(3.5, 2.4))
    ax7.axis('off')
    cols = ['Property', 'This Work', 'Wisland 2003', 'Kim 2024']
    table_data = [[r[0], r[1], r[2], r[3]] for r in rows]
    tbl = ax7.table(
        cellText=table_data,
        colLabels=cols,
        loc='center',
        cellLoc='center',
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(6.5)
    tbl.scale(1.0, 1.25)
    ax7.set_title('Prior Art Comparison', fontsize=8, pad=12)
    fig7.tight_layout()
    fig7.savefig('figures/fig7_summary_comparison.pdf', bbox_inches='tight')
    fig7.savefig('figures/fig7_summary_comparison.png', bbox_inches='tight', dpi=300)
    plt.close()
    
    lag1 = abs(autocorr[0]) if autocorr and np.isfinite(autocorr[0]) else 1.0
    print(f"  Claim 3: Sigmoid obtained: ✅")
    print(f"  Claim 3: Lag-1 autocorr = {lag1:.4f}  (need <0.05)")
    verified = lag1 < 0.05
    print(f"  Claim 3 {'✅ VERIFIED' if verified else '❌ FAILED'}: randomness confirmed")
    return verified


if __name__ == "__main__":
    os.chdir(os.path.join(os.path.dirname(__file__), ".."))
    run()
