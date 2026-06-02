"""
Claim 1: FGMOS ohmic-region R_eff is programmable via Vfg.
Generates: figures/fig2_Reff_vs_Vfg.pdf + .png
           data/claim1_Reff_sweep.csv
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from fgmos_model import FGMOSCell

plt.rcParams.update({
    'font.family': 'serif', 'font.serif': ['Times New Roman'],
    'font.size': 8, 'axes.labelsize': 8,
    'xtick.labelsize': 7, 'ytick.labelsize': 7,
    'legend.fontsize': 7, 'figure.dpi': 300
})

def run():
    os.makedirs('figures', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    cell = FGMOSCell()
    # Direct Vfg sweep — characterizes ohmic R_eff (divider gives Vfg < Vth from Vctrl alone)
    Vfg_sweep = np.linspace(0.52, 1.28, 500)
    
    R_vals = []
    for Vfg in Vfg_sweep:
        R = cell.R_eff(Vfg)
        R_vals.append(R / 1e3 if np.isfinite(R) else np.nan)
    
    # Implied Vctrl when IN1–IN3 = 0 (for cross-reference with RTL programming)
    Vctrl_implied = Vfg_sweep * cell.CT / cell.Cfg
    
    df = pd.DataFrame({
        'Vfg_eff_V': Vfg_sweep,
        'Vctrl_implied_V': Vctrl_implied,
        'Reff_kOhm': R_vals,
    })
    df.to_csv('data/claim1_Reff_sweep.csv', index=False)
    
    fig, ax = plt.subplots(figsize=(3.5, 2.8))
    R_plot = np.nan_to_num(R_vals, nan=60.0)
    R_plot = np.clip(R_plot, 0, 60)
    ax.plot(Vfg_sweep, R_plot, 'b-', linewidth=1.5, label='FGMOS $R_{eff}$')
    ax.axhline(10, color='gray', linestyle='--', linewidth=1,
               label=r'Fixed $R=10k\Omega$ (conv. RTL)')
    ax.axvspan(0.75, 1.25, alpha=0.12, color='green', label='RTL operating band')
    ax.set_xlabel('Effective FG voltage $V_{fg,eff}$ (V)')
    ax.set_ylabel(r'$R_{eff}$ (k$\Omega$)')
    ax.set_title('Claim 1: Programmable RTL Base Resistor', fontsize=8)
    ax.legend(loc='upper right', fontsize=6)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 55)
    fig.tight_layout()
    fig.savefig('figures/fig2_Reff_vs_Vfg.pdf', bbox_inches='tight')
    fig.savefig('figures/fig2_Reff_vs_Vfg.png', bbox_inches='tight', dpi=300)
    plt.close()
    
    valid = [r for r in R_vals if r is not None and 0 < r < 60 and np.isfinite(r)]
    ratio = max(valid) / min(valid) if valid else 0
    print(f"  Claim 1: R_eff range = {min(valid):.1f} – {max(valid):.1f} kΩ  (ratio={ratio:.1f}x)")
    verified = ratio >= 10
    print(f"  Claim 1 {'✅ VERIFIED' if verified else '❌ FAILED'}: R_eff spans >10x")
    return verified
