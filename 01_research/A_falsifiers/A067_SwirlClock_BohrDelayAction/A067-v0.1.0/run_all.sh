#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ "${1:-}" == "SELFTEST" ]]; then python -m unittest discover -s tests -v; exit; fi
if [[ "${1:-}" == "REVEAL" ]]; then echo 'REVEAL DENIED: scientific gates G7-G9 unresolved'; exit 4; fi
python src/run.py
python src/make_report.py
