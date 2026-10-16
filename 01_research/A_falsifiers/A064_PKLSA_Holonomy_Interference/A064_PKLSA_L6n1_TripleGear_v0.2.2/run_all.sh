#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [ "$#" -eq 0 ]; then python hopf_cli.py RUN; else python hopf_cli.py "$@"; fi
