# SST Falsifier Framework v1.1.0 — Validation

Status: **DEVELOPMENT / SOURCE-VALIDATED / TARGET-HARDWARE PENDING**.

## Source provenance
- Canonical v1.0.10 manifest reproduced **112/112 exact SHA-256 matches**.
- Canonical v1.0.7 historical source lineage retained in `docs/VALIDATION_v1.0.7.md`.
- v1.0.11 optional backend probe concept incorporated with added 2-of-3 contract and CUDA provider support.
- Parent canonical source files and freeze metadata preserved under `provenance/parent_v1.0.10/`.

## Completed model environment checks (not user's Windows hardware)
- Framework unit/regression suite: **94 PASS** after updated self-contained contract tests.
- Standalone subprocess FREEZE/FULL: **PASS** (FULL exit 3 as designed because no two genuine science backends implemented).
- Output manifest, PDF publication, unique blind ZIP and archive SHA-256: **PASS**.
- Two-run retention: **PASS**, previous directory and original PDF/ZIP preserved.
- Non-short-circuit gate run: **PASS**; G2 FAIL does not stop G3/G8 diagnostics, but downstream qualification remains DIAGNOSTIC_ONLY.
- Tamper rejection: source/hash mismatch in `_sst_runtime` prevented import.
- Python+Cpp and Python+GPU contract logic: **PASS on synthetic records/mocked probes**, not hardware execution.
- PDF 16-section heading/content validation: PASS on template, sparse marker-only report rejected.

## Explicit limitations / release blockers
- No real C++ pybind11, Intel XPU or NVIDIA CUDA numerical solver integration executed in current Linux testing environment.
- No performance or precision claim on Intel Arc A770 16 GiB or GTX 1060 6 GiB.
- The E010 v0.4.0 atlas is NOT packaged; local `ATLAS_VERIFY` against user-owned E010 ZIP and exact pinned Universal Atlas Adapter remains pending.
- Full native compiler/oneAPI/CUDA artifact verification, two genuinely executed kernels, parity, physics-specific convergence and physical acceptance gates are pending on target machine.
- The ReportLab fallback is `DEGRADED_DIAGNOSTIC_ONLY`, never a full scientific report certification.
- Existing frozen falsifiers are never silently migrated.

## Release approval rule
Do not rename to `CANONICAL_FROZEN` until target-machine qualification (Python + pybind11, Intel XPU, optional Pascal CUDA), E010 integration, and PDF visual/regression acceptance have all passed with exact source hashes.
