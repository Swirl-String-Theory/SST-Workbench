# VALIDATION — v0.2.3

Required before a scientific run:

1. `tools/preflight.py` verifies the v0.2.3 cryptographic seal.
2. Unit tests verify the frozen parent hash, unchanged legacy modal thresholds, 12 direction hashes, paired amplitude ladder, local-core rule, and Wilson-interval helper.
3. `run_all.cmd` writes resumable per-trajectory cache files and creates the final diagnostic hash.
4. The parent v0.2.2 verdict is copied into the output and is never recomputed or overwritten.
5. Numerical convergence is triggered only after the frozen finite-radius core rule succeeds.

The optimized persistence reducer was checked against the v0.2.2 implementation on an identical C00016 trajectory prefix; checkpoint mode, frequency, phase R^2, and dominant fraction agreed exactly.
