# A058-v0.3.8 validation — 2026-10-23

## Executed in this build container

- All 83 Python unit tests executed: **82 passed, 1 skipped** (the inherited Windows-specific shortcut test cannot run under Linux).
- Authentic supplied `A058_measurement_v037.zip` audited read-only: **2 positive native scalar conditions confirmed; 2 negative controls reproduced**, with recorded native log, runtime script, seed and coordinate SHA-256 consistency gates. Historical *method* closure = PASS. The two negative *measurement* gates remain FAIL.
- Original `kpdist-23mar2025.zip` was read to generate and preregister the six new v0.3.8 probe scripts; no native KnotPlot executable is present in this environment.
- A mocked six-condition end-to-end launcher test passed, verifying absolute export paths, launcher working directory, finite-time row validation, readback and non-overwrite behavior. This is a software test, not a native KnotPlot science run.
- Every inherited v0.3.7 source file not explicitly changed was checked byte-identical with the archived v0.3.7 release.

## Scientific qualification boundaries

`A058 v0.3.8` has **not** been executed against native Windows KnotPlot. The six new 32/128/512 horizon conditions are **NOT_RUN**. Historical closure only certifies that the positive/negative command-order controls reproduce the observed data-writer behavior. Physics, independent topology preservation between snapshots, fully collision-free trajectories, and converged knot equilibria remain **UNRESOLVED**.

## Core contract

For each condition, `go N` is followed by native final `parameters`/`safe` readback, then `data open; data format; data header; length; rog; data; data close; save ... ascii`. Every CSV scalar must agree numerically with independent coordinate geometry. Native exit code 0 is necessary but not sufficient. Existing 271 blind cases and their gate ledgers are untouched.
