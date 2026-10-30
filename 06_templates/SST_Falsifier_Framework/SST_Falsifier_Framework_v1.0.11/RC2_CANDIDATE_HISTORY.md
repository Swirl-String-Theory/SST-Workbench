# SST Falsifier Framework v1.0.10 — corrected release candidate RC2

**Status:** LOCAL_VALIDATED_CANDIDATE / NOT YET CANONICAL_FROZEN.

This immutable RC2 artifact supersedes the earlier `v1.0.10-CLEAN_CANDIDATE.zip` for evaluation only. The original v1.0.9 canonical remains immutable, and its freeze information is kept under `PARENT_V109_CANONICAL_FREEZE.*`.

## RC2 corrections

- Packaging version in `pyproject.toml` is now `1.0.10` (was `1.0.9`).
- Backend parity JSON gets `framework_version` from the installed package, preventing stale hardcoded versions.
- A `--skip-cpp` DD32-only run prints `SKIPPED` instead of `UNAVAILABLE/FAIL` without changing acceptance or precision thresholds.
- A misnamed file asserting that `v1.0.9` is the active `CANONICAL_FREEZE.md` was removed; v1.0.9 ancestor record is preserved separately.
- Additional release-consistency regression tests ensure version alignment.

The successful October 18 Windows run is evidence for the first v1.0.10 candidate with identical numerical kernels; it is *not* presented as an execution of this exact RC2 ZIP. Please run `run_all.cmd ALL`, `run_all.cmd DD32`, and the two smoke tests from this exact RC2 candidate before canonical promotion.

Releasing or promoting this candidate must never silently replace the SHA-256 of the first candidate.
