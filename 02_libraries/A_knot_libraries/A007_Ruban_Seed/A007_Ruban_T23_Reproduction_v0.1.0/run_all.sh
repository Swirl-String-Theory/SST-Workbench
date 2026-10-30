#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python -m pytest -q tests
if [[ "${1:-SMOKE}" == "CONVERGE" ]]; then
  python -m ruban_falsifier.convergence
else
  python -m ruban_falsifier "${1:-SMOKE}"
fi
