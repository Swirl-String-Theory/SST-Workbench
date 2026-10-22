# A003 v0.3.2.1 — forensic G5 receipt compatibility finding

## Source

User-uploaded run from `A003_Fourier_Knot_Import_Adapter_v0.3.1-outputs/20261021T035725.584510Z_3002571cc9`, internally recording `adapter_version = 0.3.2` (the output-folder version was inherited from the old CMD runner). Both subsequent v0.3.2 G6 runs referenced exactly the same three file hashes.

## First failing operation

`g6_pklsa_pilot_v029.py:g5_check`, the first part of `core_ok`:

```python
# Old, incorrect for a genuine v0.3.2 G5 qualification:
d.get('adapter_version') in ('0.2.8.1','0.2.9','0.3.0','0.3.1')
```

All other controls in `core_ok`, `ledger_ok`, and `obs_ok` passed with this **real** historical G5 receipt:

- `corrected_g5_bounded_result = PASS_INVARIANT_SCREEN_NOT_CERTIFIED`
- `measured_provider_observations = 32`, `exit_code = 0`, no `failed_gates`
- 10 mandatory G0/G1/G5Q0–G5Q7 record statuses PASS
- internal framework GateLedger SHA256 matches regenerated canonical digest
- 32 expected provider cases and the provider identifier `pyknotid`
- manifest source SHA256 unchanged

## Minimal repair

Allow explicit versions `0.3.2` and `0.3.2.1`, but not arbitrary future adapter versions. Preserve all scientific checks, hashes and fail-closed outcomes. Write new v0.3.2.1 outputs to their own folder and recognize that folder in `find_g5_summary()` to avoid mis-association with old v0.3.1 runs. The frozen atlas, Framework v1.0.10, E010 v0.3.1, C005 v0.6.1, and old output archive were not mutated.

## Validated outcome

Re-running the *real* historical G5 receipt through the repaired function produces `G5=PASS` instead of the previous false `FAIL`. 10 synthetic negative/positive regression tests PASS. Full available suite 114 total, 84 PASS, 30 external skips, 0 failures.  **No new Windows v0.3.2.1 trajectory or full Euler certification has been executed.** G6P8 and G6P9 remain `UNRESOLVED`.

## Windows instructions

Unpack the ZIP as a separate directory next to A003-v0.1.2. To consume the existing valid G5 v0.3.2 result without recomputing G5:

```bat
run_all.cmd G6
```

If a completely fresh, separate new G5 is required:

```bat
run_all.cmd COMPLETE
```

Ensure the expected Workbench dependencies, Python venv, `pyknotid==0.5.3`, and Framework v1.0.10 are available; do not change gate prerequisites to hide a missing provider.
