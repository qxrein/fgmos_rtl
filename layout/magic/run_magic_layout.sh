#!/usr/bin/env bash
# Generate / update fgmos_rtl_cell layout and run DRC (Sky130A Magic)
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [[ -z "${PDK_ROOT:-}" ]]; then
  echo "ERROR: export PDK_ROOT=<path-to-pdk>" >&2
  exit 1
fi
export PDK="${PDK:-sky130A}"

mkdir -p export

# If this is still the placeholder guide cell, recreate it to avoid stale lock state.
if [[ -f fgmos_rtl_cell.mag ]]; then
  LC="$(wc -l < fgmos_rtl_cell.mag || echo 999)"
  if [[ "${LC}" -le 10 ]]; then
    rm -f fgmos_rtl_cell.mag
  fi
fi

echo "==> Magic layout (batch)"
magic -dnull -noconsole -rcfile magrc > export/magic_layout.log 2>&1 <<'EOF'
source fgmos_rtl_layout.tcl
quit
EOF
if [[ -f export/magic_layout.log ]]; then
  if /usr/bin/grep -qi "locked by pid" export/magic_layout.log; then
    echo "ERROR: fgmos_rtl_cell.mag is locked; close stale Magic process and retry." >&2
    echo "See export/magic_layout.log for details." >&2
    exit 1
  fi
fi

if [[ -f export/fgmos_rtl_cell.gds ]]; then
  echo "==> GDS: export/fgmos_rtl_cell.gds"
else
  echo "WARN: GDS not written — open Magic GUI to complete placement:"
  echo "  magic -d XR -rcfile magrc fgmos_rtl_cell.mag"
fi

echo "==> DRC (if layout present)"
magic -dnull -noconsole -rcfile magrc > export/magic_drc.log 2>&1 <<'EOF'
load fgmos_rtl_cell
drc check
drc catchup
drc count total
quit
EOF

echo "Done. Copy export/*.gds to ../openlane/fgmos_rtl_wrapper/macros/"
