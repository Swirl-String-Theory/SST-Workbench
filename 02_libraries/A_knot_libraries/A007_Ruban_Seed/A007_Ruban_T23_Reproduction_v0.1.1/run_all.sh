#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
MODE="${1:-SMOKE}"
case "${MODE}" in
  FREEZE|CERTIFY|REVEAL) echo "Framework runtime not audited: $MODE refused" >&2; exit 4 ;;
  TEST) python -m pytest -q tests; exit $? ;;
  CONVERGE) python -m pytest -q tests; python -m ruban_falsifier.convergence; exit $? ;;
  SMOKE|BASIC|FULL) python -m pytest -q tests; python -m ruban_falsifier "$MODE"; exit $? ;;
  *) echo "Unsupported mode: $MODE" >&2; exit 4 ;;
esac
