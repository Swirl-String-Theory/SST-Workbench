# Changelog

## v0.2.4 — Ridgerunner VECT parser + auxiliary-file trust hotfix (2026-08-30)

Geometry kernels, KAtlas registry data, blind-campaign hashing and physics-facing qualification formulas are unchanged.

### Fixed

- Geomview/plCurve `VECT` tokenization now strips `#` comments before parsing.
- Added `4VECT` header support.
- Added header/count/truncation validation for VECT files.
- Ridgerunner `*.struts.vect`, `*.dlen.vect`, and `*.dVdt.vect` are classified as auxiliary diagnostics and
  `SKIPPED_NON_GEOMETRY`, never as knot/link centerlines.
- Inventory reports now include `ignored_extension_examples` (up to five paths per ignored extension).

### Evidence from the user v0.2.3 Windows scan

- `KnotPlot\knots`: 2200 VECT errors consisted only of 1907 `#` comment-tokenization failures and
  293 `*.struts.vect` non-centerline files.
- broad `KnotPlot`: 2897 VECT errors consisted only of 2544 `#` comment-tokenization failures and
  353 `*.struts.vect` non-centerline files.
- `Fremlin_FourierSeries`: 402 files discovered, including 73 `.fseries`; the Fourier syntax is intentionally
  not guessed in v0.2.4.

### Validation added

- commented `VECT` load;
- `4VECT` load;
- Ridgerunner struts/dlen/dVdt exclusion;
- ignored-extension path examples.

Python smoke/format/trust suite: 25/25 PASS in the release build environment.
Standalone C++17/OpenMP self-test: PASS.

## v0.2.3 — dataset scanner trust + inventory history hotfix (2026-08-30)

This release changes dataset discovery/audit behavior only. Geometry kernels, topology registry data,
blind-campaign hashing and physics-facing qualification formulas are unchanged from v0.2.2.

### Fixed

- Broad project scans no longer treat every `.txt` / `.csv` file as knot geometry.
- Added a fail-closed geometry-candidate classifier with strong signatures for KnotPlot 1.0, VECT,
  Brian Gilbert Fourier, `.xyz`, known KnotPlot geometry extensions and `fseries`/`ideal` names.
- Plain text/CSV is parsed only when a sampled XYZ content signature is present, or when a strong
  topology-bearing geometry filename requires a parse attempt.
- Unrelated project text is reported as `SKIPPED_NON_GEOMETRY`, not `ERROR`.
- A malformed strongly-identified geometry file remains `ERROR`; the scanner does not hide broken data.
- Inventories now report `discovered_file_count`, `selected_file_count` and
  `ignored_extension_counts`. This distinguishes "no supported files selected" from "empty directory".
- `run_dataset_inventory.cmd` writes timestamped inventory history under
  `outputs\dataset_inventories\` and also refreshes `outputs\dataset_inventory.json` for compatibility,
  preventing repeated scans from destroying the prior report.

### Validation added

- unrelated `.txt` project file -> `SKIPPED_NON_GEOMETRY`;
- ignored-extension accounting;
- topology-bearing malformed geometry remains `ERROR`.

Python smoke/format/trust suite: 23/23 PASS in the release build environment.
Standalone C++17/OpenMP self-test: PASS.
