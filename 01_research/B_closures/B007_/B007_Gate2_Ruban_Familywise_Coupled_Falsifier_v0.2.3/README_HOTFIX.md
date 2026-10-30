# B007 v0.2.3 — HF1 analytic-source parity patch

## Why this hotfix exists

The dataset files are SHA-256 verified; the previous B007 `np.array_equal(regenerated, arr)` was **bitwise** and could fail across Python/NumPy/libm builds when re-evaluating the same analytic E010 formula. This hotfix does **not** skip the test. It accepts only bounded IEEE-754 float64 rounding-scale differences, requiring BOTH:

- `max(abs(regenerated - loaded)) <= 128 * eps_float64 * coordinate_scale`;
- `rms(regenerated - loaded) <= 32 * eps_float64 * coordinate_scale`;
- `coordinate_scale = max(1, max(abs(loaded)), max(abs(regenerated)))`.

The original dataset byte SHA-256, source-generator SHA-256, config SHA-256, atlas-index pin and file/shape checks are unchanged. If Windows shows a larger discrepancy, B007 stops with quantitative details; **do not increase thresholds without investigating**.

## Apply on Windows 11 (from within existing B007 v0.2.3 root)

1. Extract `B007_v0.2.3_HF1_PATCH.zip` INTO the **existing** B007 v0.2.3 project root. The extracted folder should be `B007_v0.2.3_HF1_PATCH` alongside `run_all.cmd`.
2. Run:

```bat
py .\B007_v0.2.3_HF1_PATCH\apply_hotfix.py --target .
py -m pytest -q tests
```

This is a **hash-gated, fail-closed installer**. It refuses modified original source files, backs up both changed files under `.hotfix_backups\HF1`, and does not modify `run_all.cmd` or any dataset.

3. Re-run the same reduced-resolution smoke with a **NEW** run ID (the failed `B007_V023_QUICK_SMOKE` output directory may still exist):

```bat
run_all.cmd ATLAS --dataset-2048 "%N2048%" --dataset-4096 "%N4096%" --b0 0.20 --lambda-values 3.4 --dynamics-points 128,256 --steps 2 --final-time 0.0005 --run-id B007_V023_QUICK_SMOKE_HF1
```

4. Check `Gate2_Ruban_Familywise_Coupled_Falsifier_v0.2.3-outputs\runs\B007_V023_QUICK_SMOKE_HF1\G1_ANALYTIC_SOURCE_PARITY.json`. It records exact/roundoff-bounded source parity and numerical error. The run still ends in `HEURISTIC_UNDERRESOLVED` for the **128/256** dynamics and cannot certify stability. Never delete old incomplete outputs merely to reuse a run ID.

If the installer reports `Existing file was modified`, keep that file intact and inspect the diff before applying another patch. If source mismatch still exceeds tolerance, upload the full error (including max_abs_error), not modified datasets.

## Tests and validation

- Original existing tests updated to use the bounded comparison in the optional real-dataset test.
- New regression tests inject one float64 ULP, small finite perturbations, and deliberately large mismatches.
- Tested with real `E010_T23_PERTURBED_N2048` and `N4096` original archives on this system.
- The original full B007 v0.2.3 release remains intact, and this additive patch is distinctly versioned `HF1`.

**Scientific status:** ONLY source-parity repair; no physical stability, chaos, or Euler qualification asserted.
