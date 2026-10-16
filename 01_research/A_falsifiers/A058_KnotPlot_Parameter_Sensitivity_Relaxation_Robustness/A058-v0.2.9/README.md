# A058 v0.2.9 — GUI slider matched-budget campaign

Framework pin: **SST Falsifier Framework v1.0.8** (separate installation required).

## Commands (from instance root, Windows CMD)

```cmd
run_all.cmd BASIC
run_all.cmd 2048
run_all.cmd 32768
```

- `BASIC` or `512`: all **271** registered conditions, checkpoints 32, 128, **512**.
- `2048`: all **271** conditions, checkpoints 32, 128, 512, **2048**.
- `32768`: **selected** (up to 31), checkpoints 32, 128, 512, 2048, 8192, **32768**. Requires an earlier BASIC or 2048 run; prefers 2048 evidence.
- `run_pilot_all.cmd` is a compatibility alias for `run_all.cmd BASIC`.
- `run_all.cmd SELFTEST`, `run_all.cmd FREEZE`, `run_all.cmd FULL`, `run_all.cmd REVEAL_IF_ALLOWED` remain direct framework commands. `FULL` analyzes the current acquired run; it does **not** acquire 32768 iterations.

No arbitrary `ago 1000`. Each `go` command advances precisely to the next checkpoint, and conditions compare at equal solver counts. These are **finite-time responses**, not certified equilibria. High-budget cases are automatically selected from previously observed responses **before** their expensive runs.

Both the calibrated 300-bead shared seed and the executable are SHA-256 verified, and the installer still exports just one seed trefoil. Each condition restarts from the exact shared seed and its sector-default switch/slider values. R2 reset OFF, S3 frozen numeric default 1.40 and one independent activation control is retained. Damped + `collision fast`; no grav/anch/therm experimentation.

The registered total is **271**, not 272 (6 references, 1 activation control, 264 perturbations). Unavailable headless runtime sectors are isolated; the program optionally checks a graphics-initialized drag fallback and records any ineligible conditions as `UNSUPPORTED_RUNTIME`, not as negative slider findings. Native KnotPlot compatibility still needs validation on your Windows installation.

## Preservation and output

`campaign/runs/BASIC`, `campaign/runs/2048`, `campaign/runs/32768` retain raw source data, log summaries, selected cases, checkpoints, final coordinates and run hashes. Repeat a budget and its old run is archived with a UTC suffix. The current tier is referenced by `campaign/active_run.json`; the v1.0.8 framework adds its own non-overwriting run-ID ZIP/PDF archive. Private KnotPlot commands and stdout remain in `private/`.

Important: runtime defaults for some controls and per-sector access are conditional. The install/preflight qualifies the actual KnotPlot binary; unit/mock tests alone are not hardware certification.
