#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
MODE="${1:-FULL}"
if [[ "$MODE" == SELFTEST ]]; then python -m pytest -q tests; exit; fi
if [[ "$MODE" != BASIC && "$MODE" != FULL ]]; then echo 'Only SELFTEST BASIC FULL implemented'; exit 2; fi
python run_invariant.py --mode "$MODE"
python generate_report.py
