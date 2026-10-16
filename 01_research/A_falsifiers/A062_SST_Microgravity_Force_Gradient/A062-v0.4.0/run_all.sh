#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
MODE="${1:-BASIC}"
if [[ "$MODE" == "FREEZE" ]]; then python init_private.py; fi
python run_instance.py "$MODE"
