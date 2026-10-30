#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [ "${1:-}" = 'SELFTEST' ]; then shift; python -m pytest -q tests "$@"; else python -m ruban_equilibrium.runner "$@"; fi
