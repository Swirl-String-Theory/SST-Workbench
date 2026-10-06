# Local validation — revised A029-v0.7.0 mega patch

Validation was performed against a reconstructed A029-v0.6.0 source root using the exact sealed parent producer supplied by the v0.6 patch/output provenance.

## Parent integrity

- v0.6 `sst_lagrangian.py` expected SHA-256: `df880fdb1814ad568728506033ade1b15fde42c6726fdad854a7ecbc706136a0`
- hash after applying v0.7.0: unchanged and identical.
- v0.6 parent test SHA-256: `1b3d131f55b940f47f916f43845c24a877ac064c81afe2ef49a573ac04aad56f`
- user-supplied `A029-v0.6.0_outputs.zip` SHA-256: `f224dcffffa3f2ded3ba6140e951908e426231195051c26535f244c1758efd7f`

The revised patch is additive: it does not replace the v0.6 scientific producer.

## Static/unit validation

- Python compile check: PASS.
- Parent + v0.7 focused tests: `12 passed`.

## Two-pair Python diagnostic smoke run

Command-equivalent:

`run_specific_lagrangian_mega.py --diagnostic-python --limit 2`

Classification: `DIAGNOSTIC_LIMITED` — never production certification.

Pipeline completed through all seven ordered stages without synthetic substitution.

### P00000

Parent mode was not qualified, therefore downstream curvature certification was correctly `NOT_RUN_PARENT_MODE`.

### P00001

The stricter revised logic reproduced an important distinction:

- symmetric-detuning null: PASS;
- fitted power: `p = 2.0316822338177714` (consistent with quadratic vanishing);
- last-three finite-offset `C_k` RMS relative span: `0.01573135060205772`;
- Richardson radial-curvature certification: FAIL;
- last-three radial `C_k(0)` RMS relative span (`N=44,56,72`): `1.0635393297498872`;
- phase-aligned radial shape overlap minimum: `0.7769854033750001`.

So the earlier observation that `K_l` has a clean `Delta^2` null does **not** establish radial convergence of the local curvature.  The revised production-native run therefore has an adaptive extension to `N=88,104` when the detuning-null gate passes but radial convergence fails at `N=72`.

The Python fallback deliberately skips this expensive extension and records `SKIPPED_DIAGNOSTIC_BACKEND`.

## Downstream fail-closed behavior

No independent raw nonlinear/modal amplitude+phase series, physical closure-reference contract, clean SI-scale contract, or attosecond mapping manifest was supplied in the smoke environment.  Stages 03/04/07 therefore stayed `NOT_RUN`/pending as intended.
