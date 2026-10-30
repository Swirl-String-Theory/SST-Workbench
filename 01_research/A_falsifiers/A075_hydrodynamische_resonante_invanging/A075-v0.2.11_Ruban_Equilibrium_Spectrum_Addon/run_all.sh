#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
if [ "${1:-}" = "SELFTEST" ]; then python -m pytest -q tests; else python -m ruban_equilibrium.qualification "$@"; fi
