# A055 v0.4.0-r4 validation

**Scientific version:** v0.4.0  
**Implementation revision:** r4  
**Framework:** SST Falsifier Framework v1.0.4 CANONICAL_FROZEN  
**Date:** 2026-10-07  
**Status:** IMPLEMENTATION_REPAIRED / SCIENTIFIC PROTOCOL UNCHANGED

## Reason for r2

The r1 Windows selftest bootstrap passed, but the first framework FULL invocation exposed an A055 packaging regression:
`compound_v040.py` imported `import_a054_runner`, while `a055_science/upstream.py` no longer contained that helper.
The process log also showed a Python traceback followed by an IDE-reported exit code 0, so the batch runner was hardened to propagate non-zero return codes explicitly.

## Repairs

- Restored `import_a054_runner()` from the already validated A055 v0.3.1 implementation.
- The loader fail-closes if `blind_runner/a054_blind/certify_v020.py` is absent.
- The loader verifies the imported `a054_blind` namespace originates below the selected sealed campaign, preventing stale-module/cross-campaign mixing.
- Rewrote `run_all.cmd` with label-based explicit return-code propagation.
- Added a regression test for the isolated A054 runner helper.

## Frozen-protocol preservation

Byte-for-byte comparison against v0.4.0-r1 found **0 mismatches** across:

- `falsifier.toml`
- science/source contracts
- gate plan and blind policy
- blind/reveal commitments
- `FROZEN_PROTOCOL.json`
- report source
- BASIC/FULL/SMOKE scientific configs
- chirality/traveling/compound/pipeline scientific decision code

Frozen protocol SHA-256 remains:

`2d3ec1615b93df929c027c3235032b5308ac511913ac0527ade99cf00d08b429`

## Tests

- Python/A055 tests in release environment: **6 passed, 1 skipped**.
- The skipped test is the local native-extension build in the Linux validation runtime; the user Windows environment has pybind11 and exercises it through the normal selftest/G5 path.
- Repaired A054 `full_20261006_230912` seal verification: **PASS**.
- Real isolated A054 runner import: **PASS** for `certify_v020`, `blind_geometry`, `physics`, and `modes_v020`.
- Imported module-origin check: **PASS**; all modules resolve below the selected campaign's `blind_runner`.

## Framework disposition

No Framework v1.0.4 code change is required for this r2 issue. The missing loader was an A055 instance packaging regression.
Framework v1.0.5 remains the maintenance template recommended for future thin instances because it fixes the earlier pytest-bootstrap gap, but A055 v0.4.0-r2 remains scientifically pinned to v1.0.4.


## v0.4.0-r3 implementation maintenance

The r3 repair is outside the frozen scientific protocol. It fixes two runtime integration faults observed on the real Windows campaign: Framework v1.0.4 scanned `.venv/site-packages` as if third-party packages were A055 blind source, and the sealed A054 native extension was not reliably resolved under `a054_blind._native`. The r3 loader verifies the isolated `_native.pyd` against `RUNNER_MANIFEST.json`, loads it under the exact package namespace, and fails closed with explicit loader diagnostics.

### r3 regression checks

- A055 tests: 8 passed, 1 skipped in the Linux validation runtime; the skipped test is the Windows pybind extension build path.
- Runtime-owned `.venv/site-packages` contamination fixture: ignored as intended.
- Identical forbidden token in A055-owned source: blocked fail-closed as intended.
- A054 runner manifest parsing: PASS.
- Frozen v0.4.0 protocol is verified separately as byte-identical to r2 before packaging.


## v0.4.0-r4 Windows short-path staging

A real Windows run established that the canonical A054 `_native.pyd` had the correct sealed SHA-256 but direct import from the deeply nested archived campaign path failed with `DLL load failed ... The filename or extension is too long`. Historical A054-r2 execution provenance shows that its successful native preflight loaded the same extension from a short temporary isolated-runner path. r4 therefore stages only after verifying the source runner manifest, re-verifies the staged manifest before import, and leaves the sealed campaign untouched. A regression test requires the staged path to be shorter and byte-identical. Frozen protocol files remain unchanged.


## r5 manifest-allowlist staging validation

- A055 test suite: **10 passed, 1 skipped** in the Linux validation runtime.
- Real repaired A054 runner: source manifest **9/9 PASS**; staged manifest **9/9 PASS**.
- Regression with an injected untracked ABI-suffixed `_native.cp314-win_amd64.pyd`: artefact recorded as excluded and **not copied** to staging.
- Staged native set contains only `a054_blind/_native.pyd`.
- Canonical staged native SHA-256 remains `ba6f8c9fdbcaa2525a4268d597c697c9067a331a170bd63a04b4440d640b2645`.
- Frozen scientific protocol SHA-256 remains `2d3ec1615b93df929c027c3235032b5308ac511913ac0527ade99cf00d08b429`.
