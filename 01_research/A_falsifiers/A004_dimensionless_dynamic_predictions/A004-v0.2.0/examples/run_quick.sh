#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
python "$ROOT/src/sst_dimensionless_ratios.py" campaign \
  --config "$ROOT/configs/quick_campaign.json" \
  --output "$ROOT/outputs/quick_start"
