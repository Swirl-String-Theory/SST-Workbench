#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 tests/validate_integrated.py
if [[ "${1:-}" == 'PDF' ]]; then
  if command -v latexmk >/dev/null; then
    latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=results SST_VAM5_SST17_Integrated_Action_v0.2.0.tex
    cp results/SST_VAM5_SST17_Integrated_Action_v0.2.0.pdf ./SST_VAM5_SST17_Integrated_Action_v0.2.0.pdf
  else
    echo 'NOTE: latexmk not available; using precompiled PDF.'
  fi
fi
echo 'COMPLETE: formal regression only; no native PKLSA or 3D coupled model is certified.'
