#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONPATH="$PWD"
MODE="${1:-SELFTEST}"; shift || true
case "$MODE" in
 SELFTEST) python -m pytest -q ;;
 CENSUS) python -m src.library_census "$@" ;;
 LONG) python -m src.long_euler "$@" ;;
 ASSESS) python -m src.qualification ;;
 EULER_ALL_SCREEN) python -m src.batch_all_euler "$@" ;;
 REPORT) python -m src.release ;;
 *) echo "Unsupported mode: $MODE"; exit 2;;
esac
