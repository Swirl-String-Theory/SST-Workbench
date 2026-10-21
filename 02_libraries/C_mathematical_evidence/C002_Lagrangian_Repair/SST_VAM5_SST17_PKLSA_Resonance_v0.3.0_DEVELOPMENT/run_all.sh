#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python legacy_v020/validate_integrated.py
python tests/validate_v030.py
python src/generate_figures.py
if [[ "${1:-}" == "PDF" ]]; then
  if command -v pdflatex >/dev/null 2>&1; then
    pdflatex -interaction=nonstopmode -halt-on-error -output-directory=results SST_VAM5_SST17_PKLSA_Resonance_v0.3.0.tex >/dev/null
    pdflatex -interaction=nonstopmode -halt-on-error -output-directory=results SST_VAM5_SST17_PKLSA_Resonance_v0.3.0.tex >/dev/null
    cp results/SST_VAM5_SST17_PKLSA_Resonance_v0.3.0.pdf ./
  fi
fi
if [[ "${1:-}" == "NATIVE" ]]; then
 echo 'G5/G6 BLOCKED: no source-native PKLSA backend provided';exit 4
fi
