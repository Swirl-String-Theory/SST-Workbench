#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python -m a055_spectrum.cli selftest
python -m a055_spectrum.cli blind --config configs/ci.json --overwrite
python -m a055_spectrum.cli seal --config configs/ci.json
python -m a055_spectrum.cli reveal --config configs/ci.json
python -m a055_spectrum.cli package --config configs/ci.json
