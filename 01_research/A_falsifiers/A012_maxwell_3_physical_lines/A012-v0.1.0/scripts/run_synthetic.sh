#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}"
python examples/generate_synthetic_fixture.py
python -m sst_maxwell_blind.cli run \
  --config config/preregister.json \
  --campaign examples/synthetic_campaign/campaign.csv \
  --reduced-momentum examples/synthetic_campaign/reduced_momentum.csv \
  --storage examples/synthetic_campaign/storage_current.npz \
  --outdir examples/synthetic_campaign/results_blind
