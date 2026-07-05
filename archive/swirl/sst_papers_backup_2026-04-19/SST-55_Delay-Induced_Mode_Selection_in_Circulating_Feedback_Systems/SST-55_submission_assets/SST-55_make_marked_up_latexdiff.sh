#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./SST-55_make_marked_up_latexdiff.sh old.tex new.tex
# Produces:
#   marked_up.tex + marked_up.pdf

OLD_TEX="${1:-}"
NEW_TEX="${2:-}"

if [[ -z "$OLD_TEX" || -z "$NEW_TEX" ]]; then
  echo "Usage: $0 old.tex new.tex" >&2
  exit 2
fi

if [[ ! -f "$OLD_TEX" ]]; then
  echo "Missing file: $OLD_TEX" >&2
  exit 2
fi
if [[ ! -f "$NEW_TEX" ]]; then
  echo "Missing file: $NEW_TEX" >&2
  exit 2
fi

# latexdiff can choke on some complex environments; --flatten helps.
# If you use bib files, copy them alongside or add --bibtex.
latexdiff --flatten "$OLD_TEX" "$NEW_TEX" > marked_up.tex

pdflatex -interaction=nonstopmode -halt-on-error marked_up.tex
pdflatex -interaction=nonstopmode -halt-on-error marked_up.tex

echo "Done: marked_up.pdf" 
