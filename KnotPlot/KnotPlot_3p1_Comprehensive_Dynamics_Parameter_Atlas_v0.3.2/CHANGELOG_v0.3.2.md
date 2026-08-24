# v0.3.2

- `RUN_FAILED` is now an explicit discovery result rather than an automatic
  whole-atlas failure.
- Continuation is allowed only when `RUN_FAILED <= 10%` of the selected stage.
- A stage summary JSON records PASS/REJECTED/RUN_FAILED counts and the fraction.
- Added `run_15_diagnose_run_failed.cmd`.
- Added `run_resume_after_probe.cmd` so completed v0.3.1 probe data are reused.
- No parameter manifest, sweep values, baseline parameter assignments or KPC
  candidate definitions were changed.
