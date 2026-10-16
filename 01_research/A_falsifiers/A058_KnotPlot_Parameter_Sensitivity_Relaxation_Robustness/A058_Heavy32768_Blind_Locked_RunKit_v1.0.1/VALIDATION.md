# Validation — Heavy-32768 Locked RunKit v1.0.1

## Root cause and correction

The v1.0.0 Linux-generated `SELECTION_ENGINE_EXPECTED.json` has `selection_from = campaign/runs/2048`. The v0.2.10 source computes this string with Python `str(Path.relative_to(ROOT))`: on Windows it uses backslash separators. The v1.0.0 validator compared the entire JSON byte for byte, so cross-platform spelling alone could stop `CHECK_ONLY` before reporting the locked IDs. This is a verifier portability defect, not evidence that the original 27 conditions were reselected.

The v1.0.1 validator keeps strict structural equality, exact 27 condition IDs and order, exact source and selection metadata, and the previously committed SHA-256. Exception 1: path separators in `selection_from` only. Exception 2: bounded FP64 roundoff in `source_score`, `source_shape_distance`, `source_scalar_rel` only (`rel_tol=1e-9`, `abs_tol=1e-12`). All other mismatches fail with a precise field path. Both pre-run and post-run checks use this rule.

## Executed offline tests

- **10/10** Python stdlib regression tests PASS.
- Correct unchanged source commitment SHA-256: `11c0bb20703a8bcc7c0565620a485131a6feb36d649f21516c84f6b59be37137`.
- Recomputed `heavy_selection()` from the **actual uploaded 2048 private campaign ZIP** plus unmodified v0.2.10 source: **27/27 selected IDs and their order match the locked selection**.
- Original 2048 runlog and manifest SHA-256 agree with the expected 2048 decision.
- Synthetic Windows-style path from this actual recomputation: PASS.
- Synthetic tiny FP64 diagnostic drift: PASS.
- Deliberate changes in condition IDs, detail reasons, source hashes, large numerical drift, and source budget path: correctly rejected.
- Source v0.2.10 package, lock commitment, and `SELECTION_ENGINE_EXPECTED.json` **not modified**.

## Not tested

This Linux container cannot execute KnotPlot.exe or verify the live original Windows executable / current instance path. The user's new `CHECK_ONLY` and 32768 run are still needed. If `CHECK_ONLY` reveals another difference, the updated error includes the precise differing field; **do not bypass it** without investigation.
