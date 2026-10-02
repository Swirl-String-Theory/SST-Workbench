#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python -m pip install -q -e .
python -m pytest -q
python -m sst_bkm.campaign --config config/basic.json
python tools_make_manifest.py
