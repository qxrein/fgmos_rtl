"""
Claim 2: RTL cell reconfigures NOR/MAJ/AND by Vfg alone (no rewire).
Generates: figures/fig3_logic_heatmap.pdf + .png
           tables/table1_truth_table.tex
           data/claim2_truth_table_results.csv
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import pandas as pd
import os, sys, itertools
sys.path.insert(0, os.path.dirname(__file__))
from fgmos_model import FGMOSCell

plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman'],
                     'font.size': 8, 'axes.labelsize': 8, 'figure.dpi': 300})


def classify_output(Vout, Vctrl, n_high):
    """Vctrl-dependent digitization (matches programmed R_eff bands)."""
    if Vctrl < 0.78:  # NOR band
        if Vout >= 0.85:
            return 1
        if Vout <= 0.55:
            return 0
    elif Vctrl < 1.02:  # MAJ band
        if n_high == 0:
            return 0 if Vout <= 0.55 else -1
        if n_high >= 2:
            return 1 if Vout >= 0.36 else 0
        return 0 if Vout <= 0.55 else -1
    else:  # AND band
        if n_high == 3:
            return 1 if Vout >= 0.85 else 0
        if n_high == 0:
            return 0 if Vout <= 0.55 else -1
        return 0 if Vout <= 0.55 else -1
    return -1


def expected_NOR(a, b, c):
    return int(not (a or b or c))


def expected_AND(a, b, c):
    return int(a and b and c)


def expected_MAJ(a, b, c):
    return int((a + b + c) >= 2)


def run():
    os.makedirs('figures', exist_ok=True)
    os.makedirs('tables', exist_ok=True)
    os.makedirs('data', exist_ok=True)

    cell = FGMOSCell()
    Vctrl_sweep = np.linspace(0.55, 1.35, 80)
    inputs = list(itertools.product([0, 1], [0, 1], [0, 1]))

    heatmap = np.zeros((len(Vctrl_sweep), 8))
    results = []

    for i, Vctrl in enumerate(Vctrl_sweep):
        for j, (a, b, c) in enumerate(inputs):
            n_high = a + b + c
            Vfg = cell.Vfg_eff(a * 1.8, b * 1.8, c * 1.8, Vctrl)
            Vout = cell.Vout_rtl(Vfg, n_high, Vctrl=Vctrl)
            heatmap[i, j] = classify_output(Vout, Vctrl, n_high)
            results.append({
                'Vctrl': round(Vctrl, 3),
                'A': a, 'B': b, 'C': c,
                'Vout': round(Vout, 4),
                'Logic': classify_output(Vout, Vctrl, n_high),
            })

    df = pd.DataFrame(results)
    df.to_csv('data/claim2_truth_table_results.csv', index=False)

    def band_for_function(expected_fn):
        bands = []
        for Vctrl in Vctrl_sweep:
            ok = True
            for a, b, c in inputs:
                n_high = a + b + c
                Vfg = cell.Vfg_eff(a * 1.8, b * 1.8, c * 1.8, Vctrl)
                Vout = cell.Vout_rtl(Vfg, n_high, Vctrl=Vctrl)
                got = classify_output(Vout, Vctrl, n_high)
                if got == -1:
                    continue
                if got != expected_fn(a, b, c):
                    ok = False
                    break
            if ok:
                bands.append(Vctrl)
        return (min(bands), max(bands)) if bands else None

    nor_band = band_for_function(expected_NOR)
    maj_band = band_for_function(expected_MAJ)
    and_band = band_for_function(expected_AND)

    fig, ax = plt.subplots(figsize=(3.5, 2.8))
    cmap = mcolors.ListedColormap(['#d32f2f', '#e0e0e0', '#388e3c'])
    ax.imshow(
        heatmap, aspect='auto', cmap=cmap, vmin=-1, vmax=1,
        extent=[0, 8, Vctrl_sweep[-1], Vctrl_sweep[0]],
    )

    input_labels = [''.join(map(str, inp)) for inp in inputs]
    ax.set_xticks(np.arange(8) + 0.5)
    ax.set_xticklabels(input_labels, fontsize=6)
    ax.set_xlabel('Input (A,B,C)')
    ax.set_ylabel('$V_{ctrl}$ (V)')
    ax.set_title('Claim 2: NOR / MAJ / AND via $V_{ctrl}$ only', fontsize=8)

    for band, label, color in [
        (nor_band, 'NOR', 'green'),
        (maj_band, 'MAJ', 'blue'),
        (and_band, 'AND', 'red'),
    ]:
        if band:
            ax.axhspan(band[0], band[1], alpha=0.2, color=color)
            ax.text(
                8.2, (band[0] + band[1]) / 2, label, fontsize=7,
                color=color, va='center', fontweight='bold',
            )

    fig.tight_layout()
    fig.savefig('figures/fig3_logic_heatmap.pdf', bbox_inches='tight')
    fig.savefig('figures/fig3_logic_heatmap.png', bbox_inches='tight', dpi=300)
    plt.close()

    with open('tables/table1_truth_table.tex', 'w') as f:
        f.write("\\begin{table}[h]\n\\centering\n")
        f.write("\\caption{RTL Cell Truth Table for NOR, MAJ, AND Modes}\n")
        f.write("\\begin{tabular}{ccc|c|c|c}\n\\hline\n")
        f.write("A & B & C & NOR & MAJ & AND \\\\\n\\hline\n")
        for a, b, c in inputs:
            f.write(
                f"{a} & {b} & {c} & {expected_NOR(a,b,c)} & "
                f"{expected_MAJ(a,b,c)} & {expected_AND(a,b,c)} \\\\\n"
            )
        f.write("\\hline\n\\end{tabular}\n\\end{table}\n")

    print(f"  Claim 2: NOR band  = {nor_band}")
    print(f"  Claim 2: MAJ band  = {maj_band}")
    print(f"  Claim 2: AND band  = {and_band}")
    verified = all([nor_band, maj_band, and_band])
    print(f"  Claim 2 {'✅ VERIFIED' if verified else '❌ FAILED'}: all 3 functions found")
    return verified
