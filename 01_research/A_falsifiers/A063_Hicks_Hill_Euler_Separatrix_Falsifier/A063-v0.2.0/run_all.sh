#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
MODE="${1:-FULL}"
if [[ "$MODE" == "SELFTEST" ]]; then python -m pytest tests -q; exit 0; fi
if [[ "$MODE" != "FULL" && "$MODE" != "BASIC" ]]; then echo 'Only FULL/BASIC/SELFTEST'; exit 2; fi
python run_tube.py --mode "$MODE"
python generate_report.py
