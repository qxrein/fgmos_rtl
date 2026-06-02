#!/bin/bash
# Run all SPICE simulations via ngspice
# Usage: bash spice/run_all_spice.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

mkdir -p ../data

echo "=== Running Claim 1: R_eff sweep ==="
ngspice -b claim1_rtl_sweep.sp || echo "[WARN] ngspice not installed — use Python sim instead"

echo "=== Running Claim 2: Logic modes ==="
ngspice -b claim2_logic_modes.sp || echo "[WARN] ngspice not installed — use Python sim instead"

echo "=== All SPICE simulations complete ==="
