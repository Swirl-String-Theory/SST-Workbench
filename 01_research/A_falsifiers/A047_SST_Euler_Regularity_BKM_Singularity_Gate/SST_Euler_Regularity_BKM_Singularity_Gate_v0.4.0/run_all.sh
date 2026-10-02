#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
WB="${1:-${SST_WORKBENCH_ROOT:-$HOME/SST-Workbench}}"
CFG="${2:-config/v040_basic.json}"
PARENT="${3:-}"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel pybind11 numpy pytest
python -m pip install -e .
python -m pytest -q
ARGS=(--stage all --config "$CFG" --workbench-root "$WB")
if [[ -n "$PARENT" ]]; then ARGS+=(--parent-v030-output "$PARENT"); fi
python -m sst_bkm.campaign "${ARGS[@]}"
python tools_make_manifest.py
