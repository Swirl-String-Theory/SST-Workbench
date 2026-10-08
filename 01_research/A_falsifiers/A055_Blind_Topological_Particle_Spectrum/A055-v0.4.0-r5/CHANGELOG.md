# A055 v0.4.0-r5 — manifest-allowlisted A054 staging hotfix

- Execution-only hotfix; frozen v0.4.0 scientific protocol is unchanged.
- Fixes Windows native shadowing discovered after r4: an untracked ABI-suffixed `_native.cp314-win_amd64.pyd` could accompany the sealed `_native.pyd` in the archived A054 runner and be preferred by Python import resolution.
- Short-path staging now copies only `RUNNER_MANIFEST.json` plus exact manifest-tracked files.
- Untracked `.pyd/.dll/.so/.dylib` files are recorded as excluded diagnostics and are never staged.
- When the manifest authorizes `a054_blind/_native.pyd`, native loading is exact-name-only and rejects additional staged `_native*.pyd` candidates.
- Added regression coverage for stale ABI-suffixed native shadow artefacts.

# Changelog

## v0.4.0-r4 — 2026-10-07 — Windows short-path sealed-runner staging

- Keeps the canonical A054 campaign immutable and verifies every `RUNNER_MANIFEST.json` tracked byte before use.
- Copies the verified sealed `blind_runner` to a short `%TEMP%\a54_*\r` staging path and verifies the staged copy again before importing `a054_blind._native`.
- This reproduces the successful A054-v0.2.0-r2 isolated-native preflight strategy and avoids Windows `WinError 206` on the deeply archived campaign path.
- Clears stale `a054_blind.*` modules before staged import and records source/staged manifest verification plus staged native path length.
- Frozen v0.4.0 science protocol, thresholds, commitments and report contract are unchanged.

## v0.4.0-r3 — 2026-10-07 — blindness-scope + sealed-native loader maintenance

- Excludes runtime-owned `.venv`, build/cache and vendor directories from the Framework v1.0.4 instance-root blindness scan while retaining strict scans of A055 source and output files.
- Hash-checks and explicitly loads the sealed A054 `blind_runner/a054_blind/_native.pyd` before backend parity checks; records actionable diagnostics if loading fails.
- Adds regression coverage for runtime blindness exclusions and A054 runner-manifest native expectations.
- Frozen v0.4.0 science protocol, thresholds, commitments and report contract are unchanged.

## v0.4.0-r2 — 2026-10-07 — implementation-only runner repair

- Restores the fail-closed `import_a054_runner()` helper that v0.4.0 `compound_v040.py` requires.
- The helper is restored from the already validated A055 v0.3.1 implementation and verifies that imported `a054_blind` modules originate below the selected sealed campaign.
- Rewrites `run_all.cmd` with explicit label-based return-code propagation so a Python traceback cannot be reported as process exit code 0.
- Adds a regression test for the A054 isolated-runner import helper.
- No frozen protocol file, threshold, gate definition, blind commitment, source contract, or scientific decision rule changes.
- Remains scientifically pinned to SST Falsifier Framework v1.0.4 CANONICAL_FROZEN.

## v0.4.0-r1 — 2026-10-07 — implementation-only repair

- Fixes Windows pytest collection for the thin Framework v1.0.4 instance.
- Adds a root `conftest.py` that resolves `.sst_framework_root` before test-module imports.
- Removes the non-portable `/mnt/data/work_fw104/...` fallback from `tests/test_framework_contracts.py`.
- Does not change `falsifier.toml`, science/source contracts, gate plan, blind policy, preregistration commitments, frozen protocol, thresholds, or scientific code.
- Remains scientifically pinned to SST Falsifier Framework v1.0.4 CANONICAL_FROZEN.

## v0.4.0 — 2026-10-07

Major scientific-method revision on SST Falsifier Framework v1.0.4 CANONICAL_FROZEN.

- Replaces raw signed `+m/-m` direction as the physical decision variable with component-resolved circulation-relative purity `xi`.
- Adds exact metamorphic representation controls: cyclic origin shift, rigid rotation, component permutation, and curve-orientation reversal plus circulation-sign reversal.
- Extends analysis from the finest resolution only to the full sealed A054 resolution ladder.
- Requires directional-bias sign stability across both preregistered A054 Jacobian epsilon values.
- Requires at least three eligible modes before a sector can claim one-way bias.
- Requires same-sign recurrence in at least two circulation sectors for an anonymous robust candidate.
- Treats v0.3.1 as discovery baseline only; no independent-confirmation claim.
- Retains framework v1.0.4 C++ FP64 parity, provenance, blindness, commitments and output packaging.
- Still never launches A054 or another upstream campaign automatically.
