## v0.2.7 — streaming CLI qualification and config binding

- Fix G2/G3/G5/G8 pipeline: A058 thresholds are loaded from `configs/default.json`, not the framework TOML profile.
- Add independent persistent-stdin CLI smoke probe (`--preflight-only`) before running 271 conditions. Verify safe state, `go 32`, iteration counter, and two ASCII exports.
- Stop the campaign before all 271 conditions when common streaming state fails. Preserve diagnostic logs in `private/stream_preflight/`.
- First seven reference/control conditions abort early on failure at iteration zero; all scientific gate failures can still be independently evaluated if acquisition is valid.
- User-supplied v0.2.6 run: install 31/31 PASS but 271/271 failed iter=0, and FULL threw `KeyError: thresholds`. Exact per-condition failure causes remain unverified without private run logs.

## v0.2.7 — shared safe-seed qualification
- Fixes INSTALL TEST failure for unsafe catalogue trefoil at reset-default `close` without changing research force/collision settings.
- One-time preconditioning `fitto mindist (1.05*close_0)` prepares a common SHA-256-identified safe seed. Exactly one installation export; reload tested, `go 1` liveness and safety checked.
- All 271 conditions load the identical frozen seed file (no per-condition refine/fitto).
- Scientific contract/report explicitly bound conclusions to this initial geometry scale.

# A058 changelog

## v0.2.7 — reset-default correction and binary activation contrast

- Correct private S3 default from 1.00 to **1.40** (user-observed KnotPlot reset state).
- Register R2 reset switch **OFF**, separate from the R2 **ON** sector reference.
- Add one matched R2-OFF activation control at identical numeric S3/S4 defaults. It is analyzed independently of strength responses.
- Campaign now 271 conditions; tests, thresholds, logarithmic ladder and adaptive stopping unchanged.
- Getter-unreported S3 continues to use explicit `setter_acceptance` evidence classification; do not claim numeric roundtrip without readback.
- Remove raw GUI setter names from public campaign manifest and parameter-state logs; retain full mappings and runtime trace only in private sources.
- Extend install preflight to check reset R2 status if reported, verify frozen S3 reset numeric if reported, and exercise a no-export OFF probe.
- Keep Framework v1.0.8 strict FREEZE and private commitments distinct from prior versions.

## v0.2.4 (archived)

- First getter-unreported S3 fallback, later superseded after default correction.

- Added `run_stream_preflight.cmd` for manually qualifying the persistent CLI without launching the entire campaign.
