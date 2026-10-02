#!/usr/bin/env bash
set -euo pipefail

PYTHON="${PYTHON:-python3}"

echo "[0/4] Available 5-crossing IDs"
"$PYTHON" scripts/list_ideal_ids.py data/ideal.txt --prefix "5:"

echo "[1/4] Demo reproduce G1"
"$PYTHON" scripts/sst_ffs_00_reproduce_g1.py --demo --ell-demo 2 --outdir results/00_demo

echo "[2/4] Rosetta spectrum"
"$PYTHON" scripts/sst_ffs_01_rosetta_spectrum.py --n-line-um-inv 0.5 --ells 1 2 4 8 13 21 28 34 --outdir results/01_rosetta

echo "[3/4] Ideal knots: trefoil 3:1:1, up 5:1:2, down 6:1:1"
for KID in "3:1:1" "5:1:2" "6:1:1"; do
  SAFE="${KID//:/_}"
  "$PYTHON" scripts/sst_ffs_02_filament_projection_ideal.py \
    --curve ideal \
    --ideal-file data/ideal.txt \
    --ideal-id "$KID" \
    --natural-scale \
    --n 4096 \
    --smooth-width 9 \
    --ells 1 2 4 8 13 21 28 34 55 89 \
    --outdir "results/02_ideal_${SAFE}"
done

echo "[4/4] Attachment scans"
for SAFE in "3_1_1" "5_1_2" "6_1_1"; do
  "$PYTHON" scripts/sst_ffs_03_attachment_threshold_scan.py \
    --summary-csv "results/02_ideal_${SAFE}/sst_ffs_02_summary.csv" \
    --spectrum-csv "results/02_ideal_${SAFE}/sst_ffs_02_spectrum.csv" \
    --ells 1 2 4 8 13 21 28 34 55 89 \
    --outdir "results/03_threshold_${SAFE}"
done

echo "Done. Check the results folder."
