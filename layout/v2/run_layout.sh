#!/usr/bin/env bash
# Regenerate device cells + top cell, then run Magic DRC. Usage: bash run_layout.sh
set -euo pipefail
cd "$(dirname "$0")"
source ../../.eda/env.sh
RC=$PDK_ROOT/sky130A/libs.tech/magic/sky130A.magicrc
( cd cells && rm -f -- sky130_fd_pr__*.mag devs.mag devmap.txt && perl -e 'alarm 300; exec @ARGV' magic -dnull -noconsole -rcfile $RC gen_devs.tcl > gen.log 2>&1 )
../../.eda/venv/bin/python gen_layout.py
( cd magic && rm -f -- *.mag && cp ../cells/sky130_fd_pr__*.mag . && \
  perl -e 'alarm 300; exec @ARGV' magic -dnull -noconsole -rcfile $RC qfg_tlg.tcl > gen.log 2>&1 && \
  perl -e 'alarm 300; exec @ARGV' magic -dnull -noconsole -rcfile $RC drc.tcl > drc.log 2>&1 )
grep DRCCOUNT magic/drc.log
