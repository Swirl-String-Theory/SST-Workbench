# v0.2.4

- Extends the QHP ray from t=1.32 to t=1.40.
- 16-setting frozen extended panel.
- Does not branch new QHP values from Q20 at 200k.
- Uses the byte-identical historical i0 geometry as a common cold-start.
- Three historical overlap controls are rerun to 200k first.
- Fail-closed overlap calibration gate before any new t>1.32 dynamics.
- New states cold-start to 200k with historical checkpoint/centering cadence.
- All 16 then continue metric-neutral 200k->400k.
- 20k continuation checkpoints from 220k through 400k.
- Separate ΔL/L0 and ΔRg/Rg0 zero-track diagnostics retained.
- UTF-8 explicit for reports.
- Windows-safe source extraction.
- Runner creates output directories, verifies outputs, heartbeats every minute,
  preserves completed settings, and restarts only an incomplete setting.
