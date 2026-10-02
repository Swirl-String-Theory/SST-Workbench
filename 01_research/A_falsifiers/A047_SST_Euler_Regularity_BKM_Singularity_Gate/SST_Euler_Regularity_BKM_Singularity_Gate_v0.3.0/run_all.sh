#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
WB="${1:-${SST_WORKBENCH_ROOT:-}}"
CFG="${2:-config/e010_v031_basic.json}"
if [[ -z "$WB" ]]; then echo "ERROR: Workbench root required as arg 1 or SST_WORKBENCH_ROOT" >&2; exit 2; fi
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel pybind11 numpy pytest
python -m pip install -e .
python -m pytest -q
python -m sst_bkm.campaign --config "$CFG" --workbench-root "$WB"
python tools_make_manifest.py
