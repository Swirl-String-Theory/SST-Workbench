# v0.2.4.2 incomplete-continuation recovery

Observed analysis failure:

```text
FileNotFoundError:
out\XQHP__E08_i260000.txt
```

This is not a scientific verdict. It means analysis was invoked before every
extended-panel continuation checkpoint existed.

Recovery behavior:
- analyzer now performs a complete-file preflight and exits cleanly with a list
  of missing setting/checkpoints instead of a Python traceback;
- `run_resume_continuation_then_analyze.cmd` runs only the continuation stage;
- completed settings remain `SKIP`;
- an incomplete current setting is restarted from its frozen 200k state by the
  existing runner;
- cold-start / overlap calibration stages are not rerun;
- final analysis starts only after all required output files exist;
- cumulative rich 15-second progress logging from v0.2.4.1 is included.

Scientific impact: none. No KPC, QHP value, preregistration, checkpoint schedule,
or analysis gate is changed.
