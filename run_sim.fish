#!/usr/bin/env fish
# Fish shell — do NOT use source env/bin/activate (bash-only)
set -l ROOT (dirname (status filename))
cd $ROOT

python3 -m venv env
./env/bin/pip install -q -r requirements.txt
# optional: ./env/bin/pip install gdstk  # included in requirements.txt

set -gx MPLCONFIGDIR "$ROOT/.mplcache"
mkdir -p $MPLCONFIGDIR

./env/bin/python sim/main.py
