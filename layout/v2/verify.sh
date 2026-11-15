#!/usr/bin/env bash
# Full physical verification of the v2 cell: Magic DRC, extraction, Netgen LVS, KLayout DRC (FEOL+BEOL).
set -euo pipefail
cd "$(dirname "$0")"
bash run_layout.sh
source ../../.eda/env.sh
RC=$PDK_ROOT/sky130A/libs.tech/magic/sky130A.magicrc
( cd magic && perl -e 'alarm 300; exec @ARGV' magic -dnull -noconsole -rcfile $RC extract.tcl > extract.log 2>&1 && grep BBOX extract.log )
( cd lvs && netgen -batch lvs "../magic/qfg_tlg_lvs.spice qfg_tlg" "qfg_tlg_schematic.spice qfg_tlg" \
    $PDK_ROOT/sky130A/libs.tech/netgen/sky130A_setup.tcl lvs_report.txt > netgen.log 2>&1; grep "Final result" lvs_report.txt )
( cd klayout && perl -e 'alarm 1200; exec @ARGV' klayout -b -r sky130A_full.lydrc -rd input=$PWD/../magic/qfg_tlg.gds \
    -rd topcell=qfg_tlg -rd report=$PWD/qfg_tlg_klayout_drc_full.xml > klayout_drc_full.log 2>&1 && \
  ../../../.eda/venv/bin/python -c "
import xml.etree.ElementTree as ET
r=ET.parse('qfg_tlg_klayout_drc_full.xml').getroot(); n=len(list(r.find('items')))
print('KLAYOUT_DRC_VIOLATIONS', n)" )
