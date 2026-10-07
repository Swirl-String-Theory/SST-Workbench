#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PRESET="${1:-basic}"
python -m a055_spectrum.cli selftest
python -m a055_spectrum.cli blind --config "configs/${PRESET}.json" --overwrite --force-python
python -m a055_spectrum.cli seal --config "configs/${PRESET}.json"
python -m a055_spectrum.cli reveal --config "configs/${PRESET}.json"
python -m a055_spectrum.cli package --config "configs/${PRESET}.json"
