#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python build_ruban_family.py --mode fine --archive
