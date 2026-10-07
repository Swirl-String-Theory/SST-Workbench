#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python -m a055_spectrum.cli selftest
python -m pytest -q
python -m a055_spectrum.cli blind --config configs/ci.json --overwrite
python -m a055_spectrum.cli seal --config configs/ci.json
# CI has no A054 compound branch, so use the legacy single-knot reveal only.
python -m a055_spectrum.reveal_ci
python -m a055_spectrum.cli package --config configs/ci.json
