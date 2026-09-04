#!/usr/bin/env bash
set -euo pipefail

PYTHON="${PYTHON:-python3}"

for KID in "3:1:1" "5:1:2" "6:1:1"; do
  SAFE="${KID//:/_}"
  for N in 2048 4096 8192; do
    for SMOOTH in 5 9 15; do
      OUT="results_ext/02_ideal_${SAFE}_N${N}_S${SMOOTH}"
      "$PYTHON" scripts/sst_ffs_02_filament_projection_ideal.py \
        --curve ideal \
        --ideal-file data/ideal.txt \
        --ideal-id "$KID" \
        --natural-scale \
        --n "$N" \
        --smooth-width "$SMOOTH" \
        --ells 1 2 4 8 13 21 28 34 55 89 \
        --outdir "$OUT"

      "$PYTHON" scripts/sst_ffs_03_attachment_threshold_scan.py \
        --summary-csv "$OUT/sst_ffs_02_summary.csv" \
        --spectrum-csv "$OUT/sst_ffs_02_spectrum.csv" \
        --ells 1 2 4 8 13 21 28 34 55 89 \
        --outdir "results_ext/03_threshold_${SAFE}_N${N}_S${SMOOTH}"
    done
  done
done
