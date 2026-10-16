# A064 v0.1.1 Validation

Status: **SELF-CONTAINED MODEL INPUT QUALIFIED**; **DYNAMICAL SEPARATRIX UNRESOLVED**.

- Python regression suite: **11/11 PASS** (includes numerical controls, geometry, NDarray shape, hash/tamper guard, NPZ build roundtrip/reuse and packaged model dataset verification).
- `BUILD_NPZ --knot all --grid 31`: 3 generated datasets, each `(3,31,31,31,3)` FP64, plus strict NPZ and source-geometry SHA-256 sidecars.
- `BUILD_NPZ --knot all`: all three return `VERIFIED_EXISTING` without overwrite.
- `BUNDLED`: all three execute candidate detection and transport stages, each reports `DYNAMICAL_STATUS_UNRESOLVED` and `overall_scientific_gate=UNRESOLVED`; PDF and prototype ZIP generated.
- Not a 3D Euler solver and not a certification for a material or invariant separatrix. The 3 frames in each model are equal; there is no computed evolution.
- All input source coordinates are native unqualified KnotPlot centerlines; E011 STATIC_READY provider source qualification was not inferred from directory name.
- Framework v1.0.7 FREEZE/CERTIFY is not performed; no official signed BLIND/REVEALED archives are claimed.
- Pinned source: E010-v0.3.1 and E011-v0.3.0 Google Drive directories. The Drive search did not identify a directly usable velocity time-series NPZ to include as independent Euler evidence.

## Replication

```bat
run_all.cmd SELFTEST
run_all.cmd BUILD_NPZ
run_all.cmd BUNDLED
```

Requirements: Python 3 plus pip-installable dependencies (`requirements.txt`); the complete *input data* and source code are bundled locally.
