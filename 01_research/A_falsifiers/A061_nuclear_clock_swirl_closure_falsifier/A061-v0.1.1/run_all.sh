#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
MODE="${1:-BASIC}"
PY="${PYTHON:-python}"
if [[ -x .venv/bin/python ]]; then PY="$(pwd)/.venv/bin/python"; fi
case "${MODE^^}" in
 SETUP) "$PY" -m venv .venv; .venv/bin/python -m pip install -r requirements.txt ;;
 FETCH) "$PY" scripts/fetch_data.py ;;
 SELFTEST) "$PY" run_instance.py SELFTEST; "$PY" -m pytest -q tests ;;
 BUILD_NATIVE) "$PY" -c 'from framework_bootstrap import load_framework; load_framework(); from sst_falsifier.native_build import build_pybind; from pathlib import Path; r=build_pybind(Path.cwd(),force=True); print(r.to_dict()); raise SystemExit(0 if r.success else 1)' ;;
 CERTIFY) "$PY" run_instance.py CERTIFY; "$PY" scripts/assert_certified.py ;;
 *) "$PY" run_instance.py "${MODE^^}" ;;
esac
