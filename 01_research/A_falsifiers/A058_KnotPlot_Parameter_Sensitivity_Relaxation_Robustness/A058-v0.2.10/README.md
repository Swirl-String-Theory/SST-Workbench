# A058 v0.2.10 — GUI slider matched-budget campaign

Framework pin: **SST Falsifier Framework v1.0.8** (separate installation required).

## Commands (from instance root, Windows CMD)

```cmd
run_all.cmd BASIC
run_all.cmd 2048
run_all.cmd 32768

rem Optional: reuse the historical v0.2.9 BASIC data for heavy selection:
run_all.cmd IMPORT_BASIC "C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A058_KnotPlot_Parameter_Sensitivity_Relaxation_Robustness\A058-v0.2.9"
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

## v0.2.10 getter precision and legacy BASIC reuse

The KnotPlot parameter dump rounds numeric values to **six digits after the decimal point**. Accordingly, every condition's initial and final observed getter must agree with the expected setter **within 0.0000005**, plus negligible FP representation slack. Returned values are *display-consistent*, **not internally FP64-exact**. Numeric getters are required even for anonymous S3 (alias and sector switch mappings are in `private/axis_map.json`), eliminating the former setter-only exception. The user-confirmed 1.40 reset-default and reset-OFF switch remain unchanged.

To avoid repeating the expensive 512-step BASIC campaign, run `run_all.cmd IMPORT_BASIC "<full path to A058-v0.2.9>"` **before** `run_all.cmd 32768`. The legacy instance must contain `campaign/runs/BASIC` and its own `private` calibration and condition logs. The importer:

1. Checks the complete 271-condition design, provenance, 512 iterations, safety evidence, saved checkpoints, final coordinate hashes and raw PRIVATE getter logs.
2. Copies the historical BASIC dataset into the new instance **without modifying its original runlog**, and writes `campaign/runs/BASIC/qualification_overlay.json` as a separately auditable certificate bound to the original bytes.
3. Makes only these requalified observations eligible for heavy selection; unsupported runtime and unqualified cases remain excluded. The historical G0–G9 ledger and old BLIND outputs remain intact.

If the historical BASIC folder already exists in this new instance, import refuses to overwrite it. `32768` still verifies that the previous data and the newly qualified installation have the **same shared seed SHA-256**; otherwise it stops. `2048` is always a full 271-condition new acquisition under the corrected getters and produces its own new framework run.

The prior R4 runtime failure is **not** claimed repaired: it stays `UNSUPPORTED_RUNTIME` if its sector probes still fail. No physical convergence claim follows from matched-iteration responses.
