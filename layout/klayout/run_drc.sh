#!/usr/bin/env bash
# Batch DRC on FGMOS macro GDS (Sky130A KLayout deck)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GDS="${1:-$ROOT/layout/magic/export/fgmos_rtl_cell.gds}"
REPORT="${2:-$ROOT/data/klayout_drc_fgmos.txt}"
DRC_DECK="${PDK_ROOT:-$HOME/share/pdk}/sky130A/libs.tech/klayout/drc/sky130A.lydrc"

if [[ ! -f "$GDS" ]]; then
  echo "ERROR: GDS not found: $GDS (run make -C layout magic)" >&2
  exit 1
fi
if [[ ! -f "$DRC_DECK" ]]; then
  echo "ERROR: DRC deck not found: $DRC_DECK" >&2
  exit 1
fi

mkdir -p "$(dirname "$REPORT")"
echo "==> KLayout DRC: $GDS"
klayout -b -rd input="$GDS" -rd report="$REPORT" -r "$DRC_DECK" 2>&1 | tail -20
echo "==> Report: $REPORT"
if grep -qi "count.*0" "$REPORT" 2>/dev/null; then
  echo "DRC: clean or see report for details"
fi
