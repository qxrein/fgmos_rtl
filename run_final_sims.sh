#!/usr/bin/env bash
# run_final_sims.sh
# Run all four pending simulation items with the corrected CT=40fF model.
# Execute from the repo root with the venv active:
#
#   source env/bin/activate   # or: .venv/bin/activate on the Linux machine
#   bash run_final_sims.sh
#
# What it does:
#   1. Verifies NOR band edges (claim2_logic.py)
#   2. Runs N=500 mismatch MC and PVT sign-off (signoff_analysis.py)
#   3. Verifies SS-corner NOR operation at Vctrl=1.3V (ss_check.py -- inline below)
#   4. Regenerates figures 3, 9, 10 (done automatically by steps 1-2)
#
# After this script completes:
#   - data/claim2_truth_table_results.csv  -> exact band edges
#   - data/signoff_mismatch_mc.csv         -> MC tau distribution
#   - figures/fig3_logic_heatmap.{pdf,png} -> updated heatmap
#   - figures/fig9_signoff_pvt.{pdf,png}   -> updated PVT plot
#   - figures/fig10_mismatch_tau.{pdf,png} -> updated MC histogram
#
# Update the paper tables with the values printed to stdout.

set -euo pipefail
cd "$(dirname "$0")"

echo "=== Step 1: NOR band verification (CT=40fF) ==="
python3 sim/claim2_logic.py
echo ""

echo "=== Step 2: Sign-off analysis (PVT + mismatch MC) ==="
python3 sim/signoff_analysis.py
echo ""

echo "=== Step 3: SS-corner NOR check at recalibrated Vctrl=1.3V ==="
python3 - <<'PYEOF'
import sys, os
sys.path.insert(0, 'sim')
from fgmos_model import FGMOSCell, CornerCell
import numpy as np

ss = CornerCell(dVth=0.06, dkn=0.82, Vcc=1.60)
print(f"SS corner: Vth0={ss.Vth0:.3f}V, kn={ss.kn*1e6:.0f}uA/V2, Vcc={ss.Vcc}V")
print(f"CT = {ss.CT*1e15:.0f} fF")

vctrl_test = 1.30
n1_vfg = ss.Vfg_eff(ss.Vcc, 0, 0, vctrl_test)
n1_reff = ss.R_eff(n1_vfg)
print(f"\nVctrl={vctrl_test}V, n=1 (V1=Vcc_SS={ss.Vcc}V):")
print(f"  Vfg_eff = {n1_vfg:.4f}V  overdrive = {(n1_vfg-ss.Vth0)*1e3:.1f}mV")
if np.isfinite(n1_reff):
    kn_in = ss.kn * (2.0/0.15)
    R_nmos = 1.0 / (kn_in * (ss.Vcc - ss.Vth0))
    Vout = ss.Vcc * R_nmos / (n1_reff + R_nmos)
    print(f"  R_eff   = {n1_reff/1e3:.2f} kOhm")
    print(f"  Vout    = {Vout:.3f}V  -> {'LOW (NOR correct)' if Vout < 0.45 else 'HIGH (NOR fail)'}")
else:
    print("  R_eff = inf (below threshold -- raise Vctrl further)")

# n=0: always HIGH
n0_vfg = ss.Vfg_eff(0, 0, 0, vctrl_test)
print(f"\nVctrl={vctrl_test}V, n=0:")
print(f"  Vfg_eff = {n0_vfg:.4f}V  Vout = Vcc = {ss.Vcc}V (always HIGH, NOR correct)")

# Mismatch check at SS: what Vctrl do we need for 3sigma margin?
margin_needed = ss.Vth0 + 3*0.02  # Vth0_max at 3sigma
print(f"\nRequired Vfg for 3sigma margin at SS: {margin_needed:.3f}V")
vctrl_min = (margin_needed * ss.CT - 10e-15 * ss.Vcc) / 5e-15
print(f"Minimum Vctrl for margin: {vctrl_min:.2f}V")
PYEOF
echo ""

echo "=== All steps complete ==="
echo "Update sn-article.tex tables with:"
echo "  - Exact NOR band edges from data/claim2_truth_table_results.csv"
echo "  - Mismatch tau mean/sigma from data/signoff_mismatch_mc.csv"
echo "  - PVT tau values from data/signoff_pvt_cell.csv"
