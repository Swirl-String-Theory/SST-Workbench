# v0.2.4.1 progress-logging hotfix

Purpose: make long KnotPlot runs visibly active without changing any dynamics.

New terminal progress:
- heartbeat every 15 seconds by default;
- immediate `CHECKPOINT` line when checkpoint outputs appear;
- checkpoint number / count;
- latest and next iteration;
- stage percentage;
- time since previous checkpoint;
- learned segment speed from completed checkpoint intervals;
- estimated current-segment percentage;
- ETA to next checkpoint;
- ETA to end of current setting;
- campaign ETA once prior setting timing exists;
- latest KnotPlot log line is surfaced when it changes.

The heartbeat interval is configurable without editing scripts:

```bat
set QHP_PROGRESS_EVERY=5
run_all.cmd
```

Minimum supported interval is 2 seconds.

Scientific impact: none.

Unchanged:
- every generated KPC;
- balance_design.json;
- PREREGISTRATION.md / lock;
- extended QHP panel;
- cold-start and checkpoint cadence;
- overlap gates;
- 200k->400k continuation;
- analysis and classification thresholds.

Already completed settings remain automatically skipped on rerun.
