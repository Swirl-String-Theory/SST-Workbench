#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
python "$ROOT/src/sst_dimensionless_ratios.py" diagnose \
  --knot-id 3:1:1 \
  --label trefoil \
  --ideal-file "$ROOT/data/ideal_favorites.txt" \
  --resolution 128 \
  --epsilon 0.08 \
  --kernel rosenhead \
  --normalization fixed_length
