#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export NUMBA_NUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
python -m pytest -q tests
python src/falsifier.py "$@"
if [[ " $* " == *" --extended "* ]]; then python src/make_report.py --extended; else python src/make_report.py; fi
python src/pack_outputs.py
