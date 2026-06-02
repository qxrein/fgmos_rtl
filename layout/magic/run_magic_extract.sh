#!/usr/bin/env bash
# Run Magic extraction + optional Netgen LVS for fgmos_rtl_cell
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [[ -z "${PDK_ROOT:-}" ]]; then
  echo "ERROR: export PDK_ROOT=<path-to-pdk-root>" >&2
  exit 1
fi
export PDK="${PDK:-sky130A}"

mkdir -p export
LAYOUT_SPICE="export/fgmos_rtl_cell_extracted.spice"
rm -f "$LAYOUT_SPICE"

echo "==> Magic extraction"
magic -dnull -noconsole -rcfile magrc > export/magic_extract.log 2>&1 <<'EOF'
source fgmos_rtl_extract.tcl
quit
EOF

LVS_SETUP="$PDK_ROOT/$PDK/libs.tech/netgen/${PDK}_setup.tcl"
SCHEM_SPICE="../xschem/fgmos_rtl.sp"
LVS_LOG="export/fgmos_rtl_cell_lvs.log"

if [[ ! -f "$LAYOUT_SPICE" ]]; then
  echo "ERROR: $LAYOUT_SPICE not generated (empty/incomplete layout)." >&2
  echo "Place devices/caps in fgmos_rtl_cell.mag, then rerun make magic-extract." >&2
  exit 2
fi

if [[ -f "$LAYOUT_SPICE" && -f "$SCHEM_SPICE" && -f "$LVS_SETUP" ]]; then
  if command -v netgen >/dev/null 2>&1; then
    echo "==> Netgen LVS"
    netgen -batch lvs "fgmos_rtl_cell $LAYOUT_SPICE" \
      "FGMOS_3IN $SCHEM_SPICE" \
      "$LVS_SETUP" "$LVS_LOG" || true
    echo "==> LVS log: $LVS_LOG"
  else
    echo "WARN: netgen not found; skipped LVS"
  fi
else
  echo "WARN: Missing one of layout/schematic/setup files; skipped LVS"
fi

echo "Done."
