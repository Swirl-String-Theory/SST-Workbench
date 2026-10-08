# Framework integration

A055 v0.4.0 is generated as a thin scientific instance of `SST_Falsifier_Framework_v1.0.4-CANONICAL_FROZEN` rather than patching the v0.3.0 bespoke runner forward.

Framework v1.0.4 owns protocol freeze/verification, nonced blind/reveal commitments, gate-DAG enforcement, source/environment/output manifests, deterministic packaging, C++ build provenance and report publication.

A055 owns only the signed-travel observable, sealed-upstream parsers, anonymous discovery rule, numerical thresholds and reveal-only paired statistics.

The framework is referenced through `.sst_framework_root` and is not vendored or modified.

## v0.4.0-r2 runner repair

The r2 repair is instance-local. It restores the A054 isolated-runner loader and hardens batch return-code propagation. It does not require or apply any change to the pinned Framework v1.0.4 runtime.

## v0.4.0-r3 compatibility note

This historical v0.4.0 scientific protocol remains pinned to Framework v1.0.4. Framework v1.0.4's `assert_blind_tree()` scans the complete instance root, including a local `.venv`. r3 installs a narrow runtime compatibility wrapper before `run_mode()` that filters only runtime/build/vendor-owned path components from the framework scan. All A055-owned source, configuration, report and generated output files remain in scope. The same behavior is incorporated generically for future falsifiers in Framework v1.0.7.

r3 also hardens the sealed A054 bridge: `blind_runner/a054_blind/_native.pyd` is checked against `RUNNER_MANIFEST.json` and explicitly loaded under the `a054_blind._native` package namespace before the sealed-backend comparison.


## v0.4.0-r4 upstream native staging note

This is an A055/A054 bridge repair, not a Framework semantic change. The historic A055 v0.4.0 protocol remains pinned to Framework v1.0.4. Framework v1.0.7 is recommended for new falsifiers, but changing this frozen instance's framework pin is intentionally avoided. The A054 source runner and short staged copy are both hash-verified against the same sealed `RUNNER_MANIFEST.json`.


## r5 upstream-runner isolation

This hotfix is instance-local and does not modify SST Falsifier Framework semantics. A054 runner execution is now reconstructed from its sealed `RUNNER_MANIFEST.json` allowlist in a short temporary path; untracked native shadow artefacts are excluded from execution.
