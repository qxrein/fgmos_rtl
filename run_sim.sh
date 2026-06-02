#!/usr/bin/env bash
# Run simulations (works in bash/zsh; fish users: see run_sim.fish)
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv env
./env/bin/pip install -q -r requirements.txt
export MPLCONFIGDIR="${PWD}/.mplcache"
mkdir -p "$MPLCONFIGDIR"
./env/bin/python sim/main.py
