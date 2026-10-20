# F005 — Sloshing Data Preflight v0.1.0

**Status:** DEVELOPMENT / data source intake / NOT a certified SST falsifier.

Copy `data/f005_sloshing_preflight.py` into the `data` folder of your **actual F005 v1 instance**. The utility works offline and uses Python 3.9+ standard library only.

Expected Windows structure (your instance name can differ):

```text
F005_v1/
├── sources/
│   ├── DATASET.zip                       # Zenodo 15223412, approx. 49.9 GB
│   └── sloshing_zenodo_package_v1.0.0.zip  # Zenodo 20039757, approx. 129.2 MB
└── data/
    └── f005_sloshing_preflight.py
```

The code identifies datasets by ZIP member names as well, so archives may have been renamed. Classification does not independently prove archive provenance.

## Step 1: fast metadata-only inventory; no extraction or 50GB scan

From the F005 root in PowerShell:

```powershell
py -3 .\data\f005_sloshing_preflight.py --root .
```

Creates:

```text
outputs/data_preflight_v0.1.0/SUMMARY.md
outputs/data_preflight_v0.1.0/preflight_report.json
outputs/data_preflight_v0.1.0/manifests/*_members.csv
```

ZIP central-directory inspection is usually fast. **It does not check the integrity of all 50 GB**.

## Step 2: verify published MD5s and record SHA-256 (slow)

```powershell
py -3 .\data\f005_sloshing_preflight.py --root . --verify-hashes
```

Expected checksums from Zenodo (if the filenames and bytes are unchanged):

- `DATASET.zip`: `0cf4dc4f3a93d7898c3da72b921dce7c`, DOI https://doi.org/10.5281/zenodo.15223412
- `sloshing_zenodo_package_v1.0.0.zip`: `0c2e91f4556c7b9fd57c12721d165f95`, DOI https://doi.org/10.5281/zenodo.20039757

The hashes are computed by streaming bytes, not decompressing. The 49.9 GB read may take minutes or longer. If you have renamed the ZIPs, manually compare the calculated MD5s in `preflight_report.json` to the values above; the tool will still record SHA-256.

## Step 3: extract only the 129MB robot sloshing package

```powershell
py -3 .\data\f005_sloshing_preflight.py --root . --extract-robot
```

This extracts only these five files, if present, into `outputs/data_preflight_v0.1.0/data/robot_sloshing/raw_extracted/`:

- `INPUT_TRAIN.npy`, `OUTPUT_TRAIN.npy` (both expected shape `(9822,1500)`)
- `trajectory_metadata.csv`, `time_vector.csv`, `load_dataset.py`

The script does not execute the downloaded loader script, doesn't overwrite existing extracted files, and does not extract the large ZIP.

### First scientific tranche after ingestion

1. Register data units and time vector, and verify input/output alignment; do not refit using holdout runs.
2. Split by trajectory or excitation *before* fitting anything; fit a conventional mass-spring-damper/sloshing baseline on training runs, and evaluate holdout runs.
3. Record amplitude transfer, frequencies, damping, uncertainty, and failure cases. A lower model error does not prove SST.
4. For the large dataset, choose **one NoBody run** with a known excitation frequency and small amplitude. Inspect its file types in the generated manifest and only then implement a native CSV/MAT/PIV adapter. Keep `FloatingBody` as a separate later tranche.
5. Once known-fluid baseline works, freeze the observational dataset and independent PKLSA predictions, then build qualified framework-v1.0.7 gates. Sloshing data cannot directly certify Kelvin or inertial vortex waves.

**Do not decompress `DATASET.zip` in full** until needed. Keep `sources/*.zip` immutable. Add `outputs/` and large `sources/` ZIPs to version control ignore rules.

## Sources (citable)

```latex
\bibitem{BernardoBrito2025}
F. Bernardo and M. Brito,
``Experimental Dataset on the interaction of sloshing tank waves with a flexible floating body,''
Zenodo dataset (2025), doi:10.5281/zenodo.15223412.

\bibitem{Giulietti2026}
N. Giulietti, M. Bedodi, D. Ghavami, D. Camilotto, and H. Giberti,
``Robot-executed longitudinal sloshing dataset for rectangular tank liquid handling,''
Zenodo dataset v1.0.0 (2026), doi:10.5281/zenodo.20039757.
```
