# A068 v0.4.2 – A004 library integration patch

**Target:** separate `A068-v0.4.2` generated with original SST Framework **v1.0.8**.
Never patch/freeze `A068-v0.4.1` in place.

## What changes

- `experiment/a004_adapter.py` is the versioned A004 import API; loads `A` or `B`, chirality `orig/mirrorX`, traversal `ccw/cw`, resolutions `600/1200/2400/4800/9600`, pinned `v0.2.2`.
- `experiment/historical.py` draws geometry from **one external A004 library**, not internal `data/historical` duplicates.
- `experiment/pipeline.py` checks A004 provenance in G1 and writes `A004_IMPORT_AUDIT.json` with 40 XYZ hashes for each run. Missing or modified A004 => `G1 FAIL`, downstream physics blocked.
- `source_contract.json` binds A004 v0.2.2 manifest SHA-256 and hashes of both adapter/pilot source modules, and locates A004 under `02_libraries/A_knot_libraries/A004_historical_trefoil`.
- `science_contract.json` and `report/FALSIFIER_REPORT.tex` describe the A004 source change, 40 geometric controls, and zero independent physical providers.
- Installed A004 release is immutable: setup **creates only if absent** from exact packaged `A004_LIBRARY_PAYLOAD`; existing A004 is verified but never overwritten.
- The original A064 Euler solver and all six frozen historical-control data blobs are unchanged.

## Local evidence

- 35/35 scientific/regression tests PASS (Linux, Python, NumPy/SciPy), including adapter provenance, A/B physical-model numerical pilot, old primary run, mirror/reversal, tamper rejection, and missing external A004.
- One-command setup was exercised with a **test framework-generator harness**, `--no-freeze`. This does not certify a real Windows v1.0.8 FREEZE.
- Full FULL/CERTIFY campaign and v1.0.8 official FREEZE **not executed** in this build environment.

## Science authority

Only a dimensionless numerical 3D-Euler model is qualified. A004 inputs are historical geometries, not independent physical PKLSA providers. The physical-clock gate G3 remains **UNRESOLVED**; model pilot controls do not automatically qualify material vortex tubes, RPOs or Floquet eigenfrequencies. Do not reveal until the frozen gate policy permits it.
