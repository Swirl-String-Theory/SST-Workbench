#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export SST_WORKBENCH_ROOT="$PWD"
: "${SST_FALSIFIER_FRAMEWORK_ROOT:?Set SST_FALSIFIER_FRAMEWORK_ROOT to the authentic v1.0.10 folder}"
python run_instance.py "${1:-BASIC}"
