# A068 v0.3.0 - home PC execution, 18 October 2026

Executed in `C:\workspace\projects\SST-Workbench` using the existing A068-v0.3.0
instance and the explicitly pinned SST Falsifier Framework v1.0.8.

## Installation and preservation

- Google Drive folder: A068_PKLSA_PhaseClock.
- Requested ONE_CLICK_PRESETUP archive SHA-256:
  `55bb9380b1cc3a60fc0d3dd79d68acc1360b2715acd137376947210397080b09`.
- The streamed Drive archive and existing local archive were byte-identical.
- Verified all 36 distribution manifest entries and the manifest checksum.
- Verified all 99 framework manifest entries and its manifest checksum:
  `731ce5fa0e6a1cae8379e3142e5aee1785a7e61280aa54049995ef511fc23ec7`.
- First presetup verification stopped on missing bundled cache files. Only ten
  missing `.pytest_cache` / `__pycache__` files were copied from the verified
  distribution. No scientific file was replaced and the setup script was unchanged.
- Presetup then accepted the already frozen instance. No keys were rotated.
- FREEZE reconfirmed existing protocol bundle
  `7399a9e78cb9f5ee45844bc8481229496fe8de1bb96ddbfc2526373f16936737`.
- All 195 pre-existing non-cache files matched the preservation inventory after
  execution, with the old working output found in its framework-created archive.
- Earlier versions, results, private keys and frozen source files were preserved.

## Executed validation and campaigns

Python 3.13.9; NumPy 2.5.3; SciPy 1.17.1; pytest 9.1.1.
An explicit process-local framework override and the existing instance locator
both resolve to v1.0.8. No additional packages or native/GPU kernels were installed.

- A068 regression tests: 17 passed; exit 0.
- Official framework SELFTEST: 64 passed; exit 0.
- Official run_all.cmd FREEZE, BASIC, FULL and CERTIFY: each exit 0.
- BASIC: one 16^3 trajectory, dt=0.04, T=6, 150 steps / 151 snapshots.
- FULL and CERTIFY: independently reran five trajectories each: primary 16^3,
  spatial 24^3, half-dt 16^3, and core 0.32 / 0.48 alternatives.
- Primary FULL/CERTIFY: dt=0.04, T=20, 500 steps / 251 snapshots.

Every run has G0/G1/G2 PASS, G3 UNRESOLVED, G4-G8 NOT_RUN_PREREQUISITE,
and G9 DEFERRED. Read-only canonical reveal eligibility checks returned false
for all three runs; no REVEAL or REVEAL_IF_ALLOWED transaction was performed.

## Scientific interpretation

Actual backend: Python/NumPy FP64; authority: EULER_MODEL_SIMULATION_ONLY.
CERTIFY is the executed campaign mode, not evidence of native/GPU parity or
physical qualification. No physical intrinsic clock was established.

The primary FULL/CERTIFY trajectory has relative energy drift 8.342254462716218e-10,
relative helicity drift 7.084815464178252e-10, maximum relative divergence
8.787215805350529e-16, and maximum CFL 0.0581718652009979.

The enstrophy refinement diagnostics are separate from the G2 conservation screen:
temporal relative difference 2.0135566771611314e-9 (passes), spatial relative
difference 0.472447314642971 (fails), finite-core relative spread
0.9206530229717269 (fails). G5 itself was not executed because G3 is unresolved.

G3 remains unresolved because the source is a single KnotPlot seed without a
qualified advected material tube, full-field relative periodic orbit, independent
dynamic provider or calibrated physical time. These are upstream qualification
requirements; no thresholds or gates were weakened to bypass them.

## Artifacts and report presentation

Three official BLIND ZIPs and three official PDFs were generated with immutable
run IDs. All output manifest file hashes and archive bytes were verified; no
private keys, nonce, private mapping or revealed directory occurs in those ZIPs.

The official PDF renderer has a wide, unwrapped gate table and long source paths.
Presentation-only READABLE PDF copies were built from copies of each run's report
inputs, with wrapped columns, hashes and verbatim text. Official output files,
PDFs, manifests and BLIND archives were not altered. All pages of the readable
reports were rendered and visually inspected. Small remaining TeX overfull-box
warnings are inside the page margins; no cropped gate text remains.

See `VERIFICATION_AND_GATES.json`, `ARTIFACTS_SHA256.txt`, per-stage logs and the
presentation-only rendering script for the reproducible audit trail.
No commit, push, source refactor, protocol modification or REVEAL was performed.
