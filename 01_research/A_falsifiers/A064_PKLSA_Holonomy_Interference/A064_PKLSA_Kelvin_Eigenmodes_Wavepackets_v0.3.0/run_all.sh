#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
PYTHON=${PYTHON:-python3}
"$PYTHON" -m pip install -r requirements.txt
"$PYTHON" -m pytest -q tests
A064_PHASE=PRIMARY "$PYTHON" src/run_kelvin.py
A064_PHASE=CONTROLS "$PYTHON" src/run_kelvin.py
"$PYTHON" src/render_report.py
"$PYTHON" src/package.py
