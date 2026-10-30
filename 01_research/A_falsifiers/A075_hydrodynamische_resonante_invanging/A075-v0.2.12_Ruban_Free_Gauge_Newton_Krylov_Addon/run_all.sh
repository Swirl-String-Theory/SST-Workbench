#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
if [[ "${1:-}" == "SELFTEST" ]]; then shift; exec python -m pytest -q tests "$@"; fi
exec python -m ruban_equilibrium.gauge_runner "$@"
