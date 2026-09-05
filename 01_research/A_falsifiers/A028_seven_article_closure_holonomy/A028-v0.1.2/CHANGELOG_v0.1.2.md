# v0.1.2 — component parsing, blind-integrity, and manifest-reuse correction

This release corrects issues identified by the v0.1.1 real-dataset output audit.

## Fixed

1. **Multi-component TXT/XYZ/CSV/DAT parsing.** Blank/component separators are preserved. Legacy concatenated exports use a conservative jump fallback accepted only if every recovered segment is independently closed.
2. **G03 execution.** Recovered link components now reach pairwise Gauss-linking diagnostics. Linking is additionally resampled (BASIC 512, EXTENDED 1024) to reduce midpoint-quadrature integer residuals.
3. **Byte-stable blind freeze on Windows.** JSON is written with `write_bytes`; SHA-256 is computed from the actual saved bytes. Reveal verifies the recorded freeze and refuses a mismatch.
4. **Byte-stable private commitment.** The private mapping commitment is computed from the saved bytes and verified before reveal.
5. **Shared BASIC/EXTENDED blind manifest.** An unchanged dataset snapshot reuses the same private random seed, opaque IDs, and train/holdout partition through `results/_blind_state`.
6. **Duplicate-content collision guard.** Opaque IDs HMAC both relative path and content digest, so byte-identical coordinate files remain separate cases.

## Added

- parser method/component counts in manifests and G00;
- `scripts/selftest_blind.py`;
- `scripts/compare_manifests.py`;
- `run_all_both.cmd`;
- reveal-time source-drift reporting.

## Scientific status

G03 remains `REFERENCE_ONLY`: integer pairwise linking is a centerline diagnostic and does not identify phase-fiber or material-vorticity topology. Pairwise `Lk=0` also does not prove a multicomponent link is globally trivial. Missing physical sidecars continue to produce `INDETERMINATE`.
