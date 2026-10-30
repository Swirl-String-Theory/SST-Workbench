#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
if [ "$#" -ne 2 ];then echo 'Usage: run_dual.sh /full/path/A075-v0.2.10 /full/path/A077-v0.1.2';exit 2;fi
PYTHONPATH="$HERE${PYTHONPATH:+:$PYTHONPATH}" python -m resolver.campaign --a075-root "$1" --a077-root "$2" --grids 48 64 80 96 --time .02 --dt .001 --markers 12 --output-parent "$HERE/.."
