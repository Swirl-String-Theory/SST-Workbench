# Safety and trust model

## Rule 1 — labels are hypotheses

A file/folder label (`3.1`, `6_2`, `7-4`) is an *expected* topology, not evidence that the coordinates realize that knot.

## Rule 2 — reference != certification

The local KAtlas snapshot is a reference for PD/Gauss/DT/braid/invariants. Looking up `6_2` does not certify a user XYZ curve as `6_2`.

## Rule 3 — no silent third-party installation

Core `run_all.cmd` installs only NumPy, pybind11 and build tooling. Optional topology packages are external. Their versions are written into `runtime_validation.json` when present.

## Rule 4 — no silent lossy format decoding

KnotPlot LOCD/LOCF are supported. Quantized LOCS/LOCC are rejected by default. Unknown `fseries` syntax is rejected unless it contains explicit XYZ coordinates.

## Rule 5 — immutable references and hashes

- every source file can be SHA-256 hashed;
- every canonical resampled geometry receives a float64 geometry SHA-256;
- KAtlas snapshot bytes have a fixed SHA-256;
- blind reveals use byte-exact SHA-256 commitments.

## Rule 6 — topology before physics

Recommended final pipeline:

```text
load
 -> source hash
 -> canonical resample
 -> topology certification
 -> dimensionless geometry qualification
 -> resolution convergence
 -> blind ID
 -> Euler/Biot-Savart
 -> Hessian/eigenmodes
 -> Floquet
 -> nonlinear ringdown
```

## Rule 7 — controls stay controls

`figure8_s3` and braid-derived seeds are independent topology/embedding controls. They are not called `ideal` and are not presumed dynamically preferred.
