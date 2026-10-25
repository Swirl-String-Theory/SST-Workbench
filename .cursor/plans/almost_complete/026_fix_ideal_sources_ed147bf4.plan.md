---
name: Fix Ideal Sources
overview: TwelveData.zip en TwelveSummary.zip ophalen van katlas.org (byte-voor-byte, ongewijzigd), SOURCE/PROVENANCE bijwerken voor de nieuwe IdealLinks_* + 12-crossing zips, MANIFEST regenereren tegen de flat Ideal_Sources-layout.
todos:
  - id: dl-twelve-zips
    content: Download TwelveData.zip + TwelveSummary.zip from katlas into Ideal_Sources/ (immutable bytes; no unpack/rewrite)
    status: completed
  - id: update-source-provenance
    content: Update SOURCE.md and PROVENANCE.md for IdealLinks_* + TwelveData + TwelveSummary inventory
    status: completed
  - id: manifest-include-verify
    content: Add sst_provenance --include; regenerate and verify MANIFEST.json
    status: completed
  - id: tests-ideal-sources
    content: Add offline tests for --include filter and SOURCE/on-disk coverage
    status: in_progress
isProject: false
---

# Fix Ideal_Sources inventory

## Hard rule: downloaded files stay untouched

- All upstream `.gz` / `.zip` / `.csv` land **byte-for-byte** as served.
- **No** gunzip, unzip-to-replace, rename of payloads, EOL conversion, or re-compression.
- Existing IdealLinks_* / Ideal*.gz / `0TwelveData.csv` already on disk are **left as-is** (already size-matched to katlas); only missing archives are fetched.
- `sst_provenance.py` only **reads** them to hash into `MANIFEST.json`.

## Current state

[`SST-Workbench/Ideal_Sources/`](c:/workspace/projects/SST-Workbench/Ideal_Sources) is **flat**. Present:

- Knots: `Ideal.txt.gz`, `Ideal_11a.txt.gz`, `Ideal_11n.txt.gz`
- Links: `IdealLinks.txt.gz` + **new** `IdealLinks_10a/10n/11a1/11a2/11n1/11n2.txt.gz`
- `0TwelveData.csv` present; **`TwelveData.zip` missing**; **`TwelveSummary.zip` not yet present**
- [`MANIFEST.json`](c:/workspace/projects/SST-Workbench/Ideal_Sources/MANIFEST.json) stale (nested `knotatlas/2016-11/` paths, no IdealLinks_10/11)

## Actions

### 1. Download the two 12-crossing zips (immutable)

| File | URL | Size |
|---|---|---|
| `TwelveData.zip` | https://katlas.org/images/e/e5/TwelveData.zip | 4 726 124 B (~4.51 MB) — 2176 polylines + summary CSV |
| `TwelveSummary.zip` | https://katlas.org/images/d/d1/TwelveSummary.zip | 36 052 B — compact 12-crossing summary (ropelength / writhe / ACN table companion on [Ideal knots](https://katlas.org/wiki/Ideal_knots)) |

Save under Ideal_Sources root. After download: check sizes only; optionally list zip member names **without writing extracted copies into the archive tree**. Leave `0TwelveData.csv` as the existing standalone copy (no overwrite from zip contents).

### 2. Refresh `SOURCE.md`

Full inventory table including IdealLinks_* and both Twelve* zips; katlas Media links; retrieval dates; attribution; licence **UNRESOLVED**. Explicit note: containers are unmodified upstream bytes.

### 3. Light `PROVENANCE.md` layout sync

Update §1 file list for IdealLinks_* + `TwelveData.zip` + `TwelveSummary.zip`; restate immutable-upstream rule.

### 4. Regenerate `MANIFEST.json`

Add repeatable `--include GLOB` to [`sst_provenance.py`](c:/workspace/projects/SST-Workbench/Ideal_Sources/sst_provenance.py) `init` (avoids hashing the Thistlethwaite PDF / tool scripts). Then:

```text
python sst_provenance.py init . -o MANIFEST.json \
  --source "Retrieved from katlas.org (Ideal knots) … See SOURCE.md." \
  --include "*.gz" --include "*.zip" --include "*.csv" --include "SOURCE.md"
```

Keep per-record hashing for Gilbert `<AB>/<TL>/<HT>` (default). Verify → 0 failures.

### 5. Tests

Offline: `--include` filter; SOURCE.md basenames cover on-disk IdealLinks_* + Twelve*.zip names. No network in CI.

## Out of scope

- Restructuring into `knotatlas/2016-11/`
- Changing Ideal_Fremlin_Fseries
- Zenodo / SSTcore resource sync
- Re-downloading IdealLinks_* / Ideal*.gz already present
- Unpacking or normalizing any archive contents on disk
