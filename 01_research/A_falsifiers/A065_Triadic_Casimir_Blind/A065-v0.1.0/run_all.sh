#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [ "$#" -eq 0 ]; then set -- ALL; fi
python3 -m triadic.runner "$@"
