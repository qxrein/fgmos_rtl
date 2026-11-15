#!/usr/bin/env bash
# Run schematic FGMOS_3IN benches with Sky130 BSIM4 nfet_01v8.
# Does not invent results: exits if PDK_ROOT or ngspice is missing.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PDK_ROOT="${PDK_ROOT:-$HOME/share/pdk}"
PDK="${PDK:-sky130A}"
NFET_TT="$PDK_ROOT/$PDK/libs.ref/sky130_fd_pr/spice/sky130_fd_pr__nfet_01v8__tt.pm3.spice"
NFET_SS="$PDK_ROOT/$PDK/libs.ref/sky130_fd_pr/spice/sky130_fd_pr__nfet_01v8__ss.pm3.spice"
NFET_FF="$PDK_ROOT/$PDK/libs.ref/sky130_fd_pr/spice/sky130_fd_pr__nfet_01v8__ff.pm3.spice"
NFET_MM="$PDK_ROOT/$PDK/libs.ref/sky130_fd_pr/spice/sky130_fd_pr__nfet_01v8__mismatch.corner.spice"

if ! command -v ngspice >/dev/null 2>&1; then
  echo "ERROR: ngspice not in PATH. Cannot run Sky130 BSIM4 cross-check." >&2
  exit 2
fi
if [[ ! -f "$NFET_TT" ]]; then
  echo "ERROR: Sky130 nfet_01v8 TT model not found at:" >&2
  echo "  $NFET_TT" >&2
  echo "Set PDK_ROOT to open_pdks / google/skywater-pdk (sky130A)." >&2
  exit 2
fi

mkdir -p "$ROOT/data"
subst() {
  local src="$1" dest="$2" model="$3"
  sed -e "s|.include PDK_NFET_TT|.include \"$model\"|" "$src" > "$dest"
}

subst claim1_rtl_sweep_bsim4.sp /tmp/claim1_bsim4.sp "$NFET_TT"
echo "=== BSIM4 R_eff DC sweep (TT) ==="
ngspice -b /tmp/claim1_bsim4.sp

subst claim_transient_bsim4.sp /tmp/claim_tran_bsim4.sp "$NFET_TT"
echo "=== BSIM4 transient switching ==="
ngspice -b /tmp/claim_tran_bsim4.sp

# PVT: TT / SS / FF model files when present
if [[ -f "$NFET_SS" && -f "$NFET_FF" ]]; then
  subst claim_pvt_bsim4.sp /tmp/claim_pvt_tt.sp "$NFET_TT"
  subst claim_pvt_bsim4.sp /tmp/claim_pvt_ss.sp "$NFET_SS"
  subst claim_pvt_bsim4.sp /tmp/claim_pvt_ff.sp "$NFET_FF"
  echo "=== BSIM4 PVT (TT) ==="
  ngspice -b /tmp/claim_pvt_tt.sp
  echo "=== BSIM4 PVT (SS) ==="
  ngspice -b /tmp/claim_pvt_ss.sp
  echo "=== BSIM4 PVT (FF) ==="
  ngspice -b /tmp/claim_pvt_ff.sp
else
  echo "WARN: SS/FF nfet_01v8 models not found; skipped PVT BSIM4 sweep." >&2
fi

if [[ -f "$NFET_MM" ]]; then
  echo "WARN: mismatch Monte Carlo needs a dedicated deck with mc_mm_switch=1; not auto-run here." >&2
fi

echo "Done. CSV files under $ROOT/data/"
