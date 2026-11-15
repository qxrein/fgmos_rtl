#!/usr/bin/env bash
# Generate + verify the K-input cell: Magic DRC, extraction (LVS + PEX), Netgen LVS, KLayout DRC.
# Usage: bash verify_k.sh K
set -uo pipefail
cd "$(dirname "$0")"
[ -f ../../.eda/env.sh ] && source ../../.eda/env.sh
K=$1; N=qfg_tlg_k$K; B=../v2k/K$K
PY=${PYTHON:-$(cd ../.. && pwd)/.eda/venv/bin/python}
$PY gen_layout_k.py $K || exit 1
RC=$PDK_ROOT/sky130A/libs.tech/magic/sky130A.magicrc
cd $B/magic && rm -f -- *.mag && cp ../cells/sky130_fd_pr__*.mag .
perl -e 'alarm 600; exec @ARGV' magic -dnull -noconsole -rcfile $RC $N.tcl > gen.log 2>&1
sed "s/qfg_tlg/$N/g" ../../../v2/magic/drc.tcl > drc.tcl
sed -e "s/qfg_tlg_lvs/${N}_lvs/; s/qfg_tlg_pex/${N}_pex/; s/qfg_tlg.gds/$N.gds/; s/load qfg_tlg/load $N/; s/save qfg_tlg/save $N/" ../../../v2/magic/extract.tcl > extract.tcl
perl -e 'alarm 900; exec @ARGV' magic -dnull -noconsole -rcfile $RC drc.tcl > drc.log 2>&1; grep DRCCOUNT drc.log; head -20 drc_report.txt
perl -e 'alarm 600; exec @ARGV' magic -dnull -noconsole -rcfile $RC extract.tcl > extract.log 2>&1; grep BBOX extract.log
cd ../lvs && $PY -c "
import sys; sys.path.insert(0,'../../../../sim/v2')
from ngs import cell_subckt; from kscale import sizing
p,_=sizing($K,0.7,8.0*($K-1)); open('${N}_schematic.spice','w').write(cell_subckt(p,K=$K,name='$N'))"
netgen -batch lvs "../magic/${N}_lvs.spice $N" "${N}_schematic.spice $N" $PDK_ROOT/sky130A/libs.tech/netgen/sky130A_setup.tcl lvs_report.txt > netgen.log 2>&1; grep "Final result" lvs_report.txt
cd ../klayout && perl -e 'alarm 1800; exec @ARGV' klayout -b -r ../../../v2/klayout/sky130A_full.lydrc -rd input=$PWD/../magic/$N.gds -rd topcell=$N -rd report=$PWD/${N}_drc.xml > klayout.log 2>&1
$PY -c "
import xml.etree.ElementTree as ET
r=ET.parse('${N}_drc.xml').getroot(); it=list(r.find('items')); c={}
for i in it: k=i.find('category').text; c[k]=c.get(k,0)+1
print('KLAYOUT_DRC_VIOLATIONS', len(it), c)"
