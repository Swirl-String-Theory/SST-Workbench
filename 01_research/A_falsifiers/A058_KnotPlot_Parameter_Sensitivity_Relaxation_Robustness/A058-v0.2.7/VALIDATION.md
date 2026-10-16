# A058-v0.2.7 — Validation record

## User-machine input and diagnosed defects

- User-reported A058-v0.2.6: `31 passed`, install `PASS` (eight live sliders, one reload-safe 300-point seed).
- Full acquisition: 271/271 conditions returned `FAIL` with `iteration=0`. Thus no valid strength-response conclusion follows. The condition-specific cause cannot be determined from the top-level console transcript alone; inspect the private per-condition logs.
- Framework-v1.0.8 FULL analysis crashed at `KeyError: 'thresholds'`. The bug was confirmed: the scientific thresholds are in `configs/default.json`, while the framework profile configuration only merges TOML.

## v0.2.7 changes

- Pipeline now loads scientific thresholds from `configs/default.json`, independently of the Framework-v1.0.8 TOML config.
- Before any 271-condition campaign, a separate persistent-stdin qualification uses the install-certified seed and one default reference: initial export -> `safe` -> `go 32` -> observed iteration counter -> second export. This is a *single observation quantum*, not a fixed relaxation horizon.
- Any failing preflight returns exit code 2 with a private JSON diagnostic and private log; the 271-condition campaign never starts.
- Early reference/control failure at iteration 0 triggers fail-fast with preserved private logs and a partial runlog; no more 271 structurally identical wasted runs.
- Only real acquisition condition failures trigger nonzero process exit; on valid acquisitions independent scientific gates continue even if earlier ones FAIL.
- The install still creates exactly one shared trefoil export; the stream probe is a *separate* campaign preflight with two temporary snapshots.

## Verified locally

- Existing + new regressions: 34/34 PASS. Two new isolated stream mock tests cover accepted SAFE + `go 32` and correctly rejected unsafe initial state.
- One new scientific pipeline regression verifies that a missing/failed campaign produces diagnostic gate FAILs without `KeyError`.
- Python compilation: PASS.
- Exact loaded SST Framework-v1.0.8 science/source/gate/report validation: PASS.
- Blind forbidden-term scan: zero hits; both nonced commitments and FREEZE + frozen verification: PASS.
- ZIP integrity: PASS (recorded in release metadata below).

## Not verified locally

- Actual KnotPlot Windows build persistent-stdin behavior and its per-condition safety logging. Real hardware/device certification is **not** asserted. If the stream qualification fails, please send `private/stream_preflight/result.json` and `private/stream_preflight/stream_probe.log` for targeted diagnosis.
