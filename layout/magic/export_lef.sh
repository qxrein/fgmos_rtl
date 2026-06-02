#!/usr/bin/env bash
# Export LEF abstract for OpenLane macro (after layout complete)
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p export

magic -d XR -rcfile magrc <<'EOF'
load fgmos_rtl_cell
select top cell
lef write export/fgmos_rtl_cell.lef
quit
EOF

echo "LEF written to export/fgmos_rtl_cell.lef"
