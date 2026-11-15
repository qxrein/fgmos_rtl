#!/usr/bin/env bash
# Remaining v2 simulation campaign (run after signoff.py). Logs in data/v2/*.log
set -u
cd "$(dirname "$0")"
PY=../../.eda/venv/bin/python
D=../../data/v2
until ! pgrep -f signoff.py >/dev/null; do sleep 15; done
echo "[$(date)] retention"   ; $PY retention.py    > $D/retention.log 2>&1
echo "[$(date)] pbit_study"  ; $PY pbit_study.py   > $D/pbit_study.log 2>&1
echo "[$(date)] pnet"        ; $PY pnet.py         > $D/pnet.log 2>&1 &
echo "[$(date)] kscale"      ; NPROC=9 $PY kscale.py > $D/kscale.log 2>&1
wait
echo "[$(date)] figdata"   ; $PY figdata.py > $D/figdata.log 2>&1
echo "[$(date)] mc final"    ; NPROC=10 $PY mc.py 300 > $D/mc_tt.log 2>&1
echo "[$(date)] DONE"
