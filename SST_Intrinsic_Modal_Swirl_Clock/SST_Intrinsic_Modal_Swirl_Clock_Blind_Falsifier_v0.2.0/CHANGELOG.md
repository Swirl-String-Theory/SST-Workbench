# Changelog

## v0.2.0 — Long-Horizon Mesh-Stabilized Recurrence Gate

Major methodology release. Physics claims from v0.1.x are **not** automatically carried forward.

### Why this release exists
The v0.1.1 `T=12` campaign showed that the observation window was no longer the dominant limitation: 48/49 non-trivial carriers exceeded the Lagrangian bead-spacing quality region before the end of the run. Long Fourier/POD traces after that point could not certify shape recurrence.

### Stage A — recurrence before mechanism
- New geometry-only long-horizon Stage A.
- `BASIC stage_a_t_final = 24`.
- `EXTENDED stage_a_t_final = 36`.
- Absolute `discovery_time = 1.2`; it no longer scales with total duration.
- Early POD modes are frozen and used unchanged over the long holdout.
- Two independent modal channels:
  - `natural`: unperturbed `arm=0` carrier motion;
  - `odd`: matched `(+eps - -eps)/(2 eps)` linear response.
- A third unperturbed arm is now generated for every carrier.
- Even-in-probe contamination is measured for the odd channel.

### Geometry-only mesh stabilization
- Adds a **tangential-only redistribution velocity** toward uniform arclength.
- No explicit normal redistribution force is added.
- Stage A uses a uniform global-volume core law `a^2 L = const` by default, because local material labels are intentionally not interpreted while the numerical mesh slides tangentially.
- Hard mesh-quality stop remains active.
- Mesh/physical RMS velocity ratio is reported for audit.

### Stronger recurrence certification
A Stage-A candidate must pass all of:
1. intrinsic modal energy/amplitude;
2. >=4 BASIC or >=6 EXTENDED holdout cycles;
3. spectral + harmonic consistency;
4. multi-return phase-space closure at `T, 2T, 3T, 4T`;
5. period stationarity across cycles;
6. amplitude stationarity across cycles;
7. low cycle-mean drift;
8. mesh-quality/completion gates.

### Stage B — causal mechanism only after recurrence
- Material-core and fixed-core branches run **only for Stage-A candidate carriers**.
- No remeshing is used in Stage B.
- Stage-A spatial modes are frozen and reused; Stage B cannot learn a more favorable mode.
- Tests stretch -> delayed modal acceleration, discovery-only delay selection, phase-scramble null, zero-lag advantage, and material-vs-fixed specificity.

### Resolution
- N=64/96/128 ladder certifies Stage-A recurrence only.
- Same anonymous carrier + same modal channel must persist.
- Period and multi-return closure must converge.

### Numerical safeguards retained
- RK4.
- `dt ~ ds^2` with a hard step cap; never silently enlarges dt.
- `py::ssize_t` MSVC portability guard.
