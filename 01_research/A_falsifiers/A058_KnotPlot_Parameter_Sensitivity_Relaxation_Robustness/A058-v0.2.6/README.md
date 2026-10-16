# A058 v0.2.6 — Trefoil slider-response and matched R2 activation control

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

## Shared safe trefoil seed (v0.2.6)
The install test prepares one 300-bead trefoil from `load 3.1`, `refine nbeads 300`, then applies **one geometry-only** `fitto mindist (1.05 * measured close default)`. It checks `safe`, exports exactly one ASCII geometry, reloads that identical file, checks safety and dynamics with `go 1`, and stores its SHA-256 under `private/install_test_runtime/defaults.json`. All 271 production conditions load those identical bytes. This is **not** an unmodified catalogue embedding; it keeps KnotPlot dynamics/default parameters unchanged but necessarily selects an absolute initial geometry scale. If the seed cannot be made safe or a reload is unsafe, installation fails closed. No per-condition `fitto`, `refine` or `ago 1000` is used.
