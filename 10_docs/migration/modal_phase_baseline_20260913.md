# Modal-phase P0 baseline (2026-09-13)

Parent scientific artefacts remain frozen. This record captures the pre-implementation test matrix.

## Parent versions

| Pack | Latest parent | Package identity (stale vs dir) |
|------|---------------|----------------------------------|
| A034 | v0.2.1 | `__version__=0.1.3` |
| A037 | v0.3.1 | `__version__=0.2.0` |
| A038 | v0.4.0 | `__version__=0.3.3` |
| A029 | v0.2.0 | `__version__=0.1.2` |

## Test matrix (pre-edit)

| Step | Result | Notes |
|------|--------|-------|
| `pytest 07_scripts/test_paper_upgrade_{certificate,certs,gates}.py` | PASS | Frozen parent pins (A034-v0.2.0 / A037-v0.3.0 / A038-v0.4.0) |
| `pytest 07_scripts/test_catalog_{registry,skeleton}.py` + hierarchy | 6 FAIL / 48 PASS overall | `test_catalog_registry.py` fails on pre-existing `FAMILY (1).yaml` / unversioned metadata; not introduced by this release |
| A034 `paper_upgrade/gate.py --selftest` | PASS | |
| A034 `pytest tests` via `PYTHONPATH=src` | PASS | no pack venv |
| A037 `paper_upgrade/gate.py --selftest` | PASS | |
| A037 `python -m sst_chiral.selftest` | FAIL | native extension required; no pack venv |
| A038 `paper_upgrade/gate.py --selftest` | PASS | |
| A038 `.venv pytest tests` | PASS | |
| A029 `paper_upgrade/gate.py --selftest` | PASS | |
| A029 `.venv pytest` | PASS | |

## Overnight certificates on disk (gitignored; hashed, not copied)

- `A034-v0.2.1/outputs/basic/paper_upgrade/certificate.json` — CAMPAIGN, `ENERGETICALLY_ADMISSIBLE`, `promotion_allowed=true`
- `A037-v0.3.1/outputs/basic/paper_upgrade/certificate.json` — CAMPAIGN, selection matrix `[[1,0,0],[0,1,1],[0,1,1]]`
- `A038-v0.4.0/outputs/basic/paper_upgrade/upstream_certs.json` — real A034/A037 + fixture geometry/mesh
- A029 sealed case JSON: **not recovered** under `A029-v0.2.0/outputs` (empty/absent). P2 residual scoring must emit `INDETERMINATE_MISSING_BASELINE_CASES`.

## Target / return-time dependency DAG

Existing `delay.py::wavepacket_return` constructs both \(\Phi_{\rm loop}\) and \(\tau_{\rm return}\) from \(\omega(k)\), \(v_g\), and the fitted synthetic envelope. Both are `derived_from_predictors` / `derived_from_predicted_dispersion`.

## Immutable pointer

`10_docs/migration/paper_upgrade_run_log_20260911_225901.md`

Final release note: `10_docs/migration/modal_phase_first_release_20260913.md`
