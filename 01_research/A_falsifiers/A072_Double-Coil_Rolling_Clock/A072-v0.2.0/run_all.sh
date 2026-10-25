#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 test_gates.py
for k in 0 1 2 3 4; do python3 chunk_runner.py --chunk "$k" --steps 3500 --N 288 --prefix main; done
python3 chunk_runner.py --chunk 0 --steps 3500 --N 192 --prefix n192
python3 chunk_runner.py --chunk 0 --steps 7000 --dt 0.0000075 --N 288 --prefix n288_halfdt
for k in 0 1; do python3 chunk_runner.py --chunk "$k" --steps 3500 --N 384 --prefix n384; done
for k in 0 1 2 3; do python3 chunk_runner.py --chunk "$k" --steps 2000 --N 512 --prefix n512; done
for k in 0 1; do python3 chunk_runner.py --chunk "$k" --steps 2000 --dt 0.0000075 --N 512 --prefix n512_halfdt; done
python3 analyze_runs.py
