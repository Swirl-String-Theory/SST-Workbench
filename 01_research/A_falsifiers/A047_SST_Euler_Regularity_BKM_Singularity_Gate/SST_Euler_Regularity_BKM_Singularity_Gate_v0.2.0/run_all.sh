#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PKLSA="${1:-${SST_PKLSA_ROOT:-}}"
CFG="${2:-config/pklsa_basic.json}"
if [[ -z "$PKLSA" ]]; then echo "PKLSA root required: ./run_all.sh /path/to/SST_Parametric_Knot_Link_Seed_Atlas_v0.1.1 [config]"; exit 2; fi
python -m pip install -e .
python -m pytest -q
python -m sst_bkm.campaign --config "$CFG" --pklsa-root "$PKLSA"
python tools_make_manifest.py
