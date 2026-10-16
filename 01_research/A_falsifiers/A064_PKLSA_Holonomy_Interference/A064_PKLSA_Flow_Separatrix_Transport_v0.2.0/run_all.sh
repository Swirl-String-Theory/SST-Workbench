#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mode="${1:-EULER_RUN}"
if [[ "$mode" == 'SELFTEST' ]]; then
   python -m euler_extension.cli EULER_TEST
elif [[ "$mode" == 'REPORT' ]]; then
   python -m euler_extension.stretchaudit
   python -m euler_extension.resolution_screen
   python -m euler_extension.report
elif [[ "$mode" == 'BUILD_NPZ' ]]; then
   shift
   python -m euler_extension.cli EULER_BUILD "$@"
elif [[ "$mode" == 'CERTIFY' || "$mode" == 'FREEZE' ]]; then
   echo 'Not certified by SST Framework v1.0.7: fail closed' >&2
   exit 3
else
   python -m euler_extension.cli "$@"
   if [[ "$mode" == 'EULER_RUN' ]]; then
       python -m euler_extension.stretchaudit
       python -m euler_extension.resolution_screen
       python -m euler_extension.report
   fi
fi
