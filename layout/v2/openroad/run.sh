#!/usr/bin/env bash
# Usage: bash run.sh <top>   (runs Yosys synthesis + OpenROAD place & route)
set -euo pipefail
cd "$(dirname "$0")"
source ../../../.eda/env.sh
TOP=$1
LIB=$PDK_ROOT/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
mkdir -p out
sed -e "s#TOP#$TOP#g" -e "s#LIB#$LIB#g" synth.ys.tmpl > out/$TOP.ys
yosys -q -l out/$TOP.yosys.log out/$TOP.ys
UTIL=${UTIL:-50} TOP=$TOP TRACKS_TCL=$PWD/tracks.tcl openroad -exit -no_init pnr.tcl > out/$TOP.openroad.log 2>&1 || { tail -30 out/$TOP.openroad.log; exit 1; }
cat out/$TOP.metrics.txt
