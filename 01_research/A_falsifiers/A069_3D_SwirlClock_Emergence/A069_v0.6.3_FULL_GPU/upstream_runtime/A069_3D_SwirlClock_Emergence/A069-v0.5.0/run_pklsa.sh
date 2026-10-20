#!/bin/sh
set -eu
cd "$(dirname "$0")"
python run_python.py -m experiment.pklsa "$@"
