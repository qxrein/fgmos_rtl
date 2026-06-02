#!/usr/bin/env bash
# Run OpenLane 2 on the digital wrapper (Docker or local install)
set -euo pipefail
DESIGN_DIR="$(cd "$(dirname "$0")/fgmos_rtl_wrapper" && pwd)"
REPO="$(cd "$DESIGN_DIR/../../.." && pwd)"

if [[ ! -f "$DESIGN_DIR/macros/fgmos_rtl_cell.gds" ]]; then
  echo "WARN: macros/fgmos_rtl_cell.gds missing — run: make -C $REPO/layout magic"
fi

if command -v openlane >/dev/null 2>&1; then
  openlane "$DESIGN_DIR"
elif docker info >/dev/null 2>&1; then
  docker run --rm \
    -v "$REPO:$REPO" \
    -v "${PDK_ROOT:-$HOME/share/pdk}:${PDK_ROOT:-$HOME/share/pdk}" \
    -e PDK_ROOT="${PDK_ROOT:-$HOME/share/pdk}" \
    -e PDK=sky130A \
    -e STD_CELL_LIBRARY=sky130_fd_sc_hd \
    efabless/openlane:latest \
    --mount-design "$DESIGN_DIR"
else
  echo "Install OpenLane 2 or Docker image efabless/openlane"
  exit 1
fi
