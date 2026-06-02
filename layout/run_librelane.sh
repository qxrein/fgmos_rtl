#!/usr/bin/env bash
# Run LibreLane from ~/projects/librelane (nix develop)
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
LIBRELANE_ROOT="${LIBRELANE_ROOT:-$HOME/projects/librelane}"
DESIGN_DIR="$REPO/layout/librelane/fgmos_rtl_wrapper"
PDK_ROOT="${PDK_ROOT:-$LIBRELANE_ROOT/pdks/ciel/ciel}"

echo "==> LibreLane root: $LIBRELANE_ROOT"
echo "==> Design dir:     $DESIGN_DIR"
echo "==> PDK root:       $PDK_ROOT"

[[ -d "$LIBRELANE_ROOT" ]] || { echo "ERROR: librelane not at $LIBRELANE_ROOT" >&2; exit 1; }

cd "$LIBRELANE_ROOT"
nix develop --command env PDK_ROOT="$PDK_ROOT" \
  python3 -m librelane --pdk-root "$PDK_ROOT" "$DESIGN_DIR/config.yaml"

GDS=$(find "$DESIGN_DIR/runs" -path '*/final/gds/*.gds' -type f 2>/dev/null | sort -r | head -1)
if [[ -z "$GDS" ]]; then
  GDS=$(find "$DESIGN_DIR/runs" -path '*/final/*/*.gds' -type f 2>/dev/null | sort -r | head -1)
fi

if [[ -n "$GDS" ]]; then
  echo "==> Found GDS: $GDS"
  export OPENLANE_GDS="$GDS"
  PYTHON="$REPO/env/bin/python"
  [[ -x "$PYTHON" ]] || PYTHON=python3
  "$PYTHON" "$REPO/layout/scripts/render_openlane_figure.py"
else
  echo "WARN: No GDS under $DESIGN_DIR/runs — check LibreLane log" >&2
  exit 1
fi
