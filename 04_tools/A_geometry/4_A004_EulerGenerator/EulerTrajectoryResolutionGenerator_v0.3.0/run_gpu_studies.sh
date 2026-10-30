#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python -m resolver.gpu_studies "$@"
