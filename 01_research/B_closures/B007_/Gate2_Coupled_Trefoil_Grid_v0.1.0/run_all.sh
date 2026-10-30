#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export NUMBA_NUM_THREADS=2 OMP_NUM_THREADS=2
python -m pytest -q tests
python src/euler_coupled.py --seed both --n 32 --steps 3
python src/assess.py
