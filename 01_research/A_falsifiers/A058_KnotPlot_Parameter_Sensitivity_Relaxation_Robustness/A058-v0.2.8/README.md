# A058 v0.2.8 — Trefoil slider-response and matched R2 activation control

Framework **v1.0.8**; trefoil 3.1, 300 beads, Damped + collision avoidance.

**Correction:** reset R2 switch is OFF; user-confirmed anonymous S3 reset default is **1.40**, not 1.00. The six sector-on references continue to be used for the eight slider curves; specifically, the R2 ON reference uses S3=1.40. One additional R2-OFF matched control uses the same numeric S3/S4 defaults. The binary activation comparison is **separate** from the S3/S4 strength fits. S3 is still getter-unreported in the user's build and validated with a preregistered setter-acceptance test, with its evidence limitation retained.

**Design:** 6 sector-ON references + 1 sector-OFF reference/control + 8×33 non-default slider values = **271 conditions**. The ladder is `m=2^(k/4), k=-16..16`, plus one exact zero per axis. It is not a fitted parabola by assumption; any quadratic in `log2(m)` is descriptive only.

**Adaptive:** `go 32` is an observation quantum, not a fixed final relaxation length. Four consecutive stable windows after warmup trigger convergence; reaching the cap is nonconvergence. No overrides for non-slider relaxation controls.

**Install:** `run_install.cmd` probes six sector contexts, confirms the separate reset R2 state when runtime-reportable, checks setter behavior, performs **exactly one** trefoil ASCII export with `go 1`, and performs a separate no-export R2-OFF setter probe. Installation stops on command errors and invalid seed safety.

**Run:**

```bat
cmd.exe /c run_pilot_all.cmd
```

The private mapping identifies the actual GUI controls; blind public analysis uses S0–S7 and R0–R5. The velocity-dependent lane under Damped remains regime-qualified, not a physical stability demonstration.

## Shared safe trefoil seed (v0.2.8)
The install test prepares one 300-bead trefoil from `load 3.1`, `refine nbeads 300`, then applies **one geometry-only** `fitto mindist (1.05 * measured close default)`. It checks `safe`, exports exactly one ASCII geometry, reloads that identical file, checks safety and dynamics with `go 1`, and stores its SHA-256 under `private/install_test_runtime/defaults.json`. All 271 production conditions load those identical bytes. This is **not** an unmodified catalogue embedding; it keeps KnotPlot dynamics/default parameters unchanged but necessarily selects an absolute initial geometry scale. If the seed cannot be made safe or a reload is unsafe, installation fails closed. No per-condition `fitto`, `refine` or `ago 1000` is used.


## v0.2.8 — Streaming CLI preflight

Before 271 research conditions the runner performs one actual persistent-stdin KnotPlot session and checks `safe`, `go 32`, iteration advance and ASCII files. Run only this diagnostic via `run_python.cmd tools\run_knotplot_campaign.py --preflight-only`. If it fails, inspect `private/stream_preflight/result.json` and `stream_probe.log`.
The install contract still exports exactly one shared trefoil; the streaming preflight is a separate campaign qualification with two temporary measurement snapshots. No fixed terminal iteration count.

### Independent one-condition stream qualification

To diagnose the failed v0.2.6 acquisition without running 271 conditions:

```cmd
run_install.cmd
run_stream_preflight.cmd
```

The preflight uses the install-qualified trefoil, one default reference from the scientific run, then `go 32` as a **measurement quantum**, not a predetermined relaxation endpoint. It writes one before/after coordinate pair under `private/stream_preflight/`, not a scientific result or an extra install export. If this fails, do not run the full campaign. Upload `private/stream_preflight/result.json` and `private/stream_preflight/stream_probe.log` for diagnosis. Those files may include the KnotPlot installation path and private command names, so share them only in an appropriate private context.


## v0.2.8 — stdout/stderr safety interleaving

KnotPlot build 5125W sometimes prints a diagnostic between `Current position is` and `safe.`. The runner now records `SAFE_WITH_WARNING` separately from `UNSAFE` and `UNCONFIRMED`. This prevents a false negative but does **not** establish full geometric validity; the warning remains recorded, and complete trajectory/safety/parameter-state validation is still required. First execute `run_install.cmd` followed by `run_stream_preflight.cmd` before any large campaign. Private diagnostic: `private/stream_preflight/result.json`.
