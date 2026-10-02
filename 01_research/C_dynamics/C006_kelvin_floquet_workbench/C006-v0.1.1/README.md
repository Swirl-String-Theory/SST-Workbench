# SST Kelvin/Floquet Workbench — C++17/pybind11 v0.1.1

Four-phase, target-blind numerical workbench inspired by *Experimental evidence of Kelvin-wave turbulence along a vortex core* and adapted to the SST vortex-filament research programme.

The package follows the established SST C++/Python pattern:

- `cpp/native.cpp` — C++17/pybind11 kernels;
- `sst_kelvin_workbench/` — Python orchestration plus a pure-Python numerical fallback;
- source-hash native rebuild through `build_ext_if_needed.py`;
- `run_phase1.cmd` ... `run_phase4.cmd` for staged runs;
- **`run_all.cmd`** for a one-command Windows audit;
- JSON + CSV outputs with explicit PASS/WARN/SKIP/DIAGNOSTIC classifications.

## v0.1.1 Windows native-build hotfix

This release fixes the two build failures observed with Python 3.14 + Strawberry/MinGW + setuptools 84 on Windows. The direct linker now requests one detected CPython import library (normally `python314.lib` -> `-lpython314`), and the setuptools fallback explicitly declares the `sst_kelvin_workbench` package so flat-layout auto-discovery is never invoked. Scientific K0--K14 logic is unchanged.


## One-command use on Windows

```bat
run_all.cmd
```

runs the `quick` preset. For the higher-resolution campaign:

```bat
run_all.cmd full
```

`run_all.cmd` creates/repairs `.venv`, installs requirements, builds the native extension, verifies that C++ is actually loaded, runs pytest, and then executes all four phases into a timestamped `audit_out_*` directory.

## Scientific scope

The package deliberately distinguishes three levels:

1. **paper benchmark** — equations/parameters taken from the Kelvin-wave experiment;
2. **regularized filament model** — a midpoint regularized Biot–Savart centerline closure used for numerical falsification experiments;
3. **SST diagnostics** — SST constants set the natural dimensionless scales, but no target value of the fine-structure constant is available to the blind solver.

It does **not** claim that the regularized filament closure is a derived finite-core SST Euler solution. It also does not call an unforced finite-time transfer experiment “stationary turbulence.”

## Canonical SST scales used

```text
v_swirl = 1.09384563e6 m s^-1
r_c     = 1.40897017e-15 m
Gamma_SST = 2*pi*r_c*v_swirl
          = 9.683619203488876e-9 m^2 s^-1
v_swirl/r_c = 7.763440655383073e20 s^-1
f0           = 1.2355899557047996e20 Hz
```

The dimensionless long-wave Kelvin benchmark is

\[
\hat\omega(x)
=-\frac12x^2\left[\ln\left(\frac{2}{x}\right)-\gamma_E+\frac14\right],
\qquad x=|k|r_c,
\]

when \(\Gamma=2\pi r_c\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}\).

## Four phases

### Phase I — K0–K3: benchmark and weak-amplitude physics

- **K0** reproduces the Rankine-vortex bending branch numerically and verifies both the small-\(ka_0\) Kelvin asymptotic and a genuinely large-\(ka_0\) asymptotic point.
- **K1** evaluates SST dimensionless scales and compares long-wave versus an alternative core-profile dispersion as a sensitivity diagnostic.
- **K2** compares C++ and Python kernels for Kelvin functions and regularized Biot–Savart velocity.
- **K3** excites a single ring mode at several amplitudes and fits the leading nonlinear frequency shift.

### Phase II — K4–K6: ring → trefoil → strict Floquet gate

- **K4** obtains finite-difference ring eigenfrequencies at two resolutions and separates curvature effects from the straight-filament asymptotic.
- **K5** evaluates the pre-registered Kelvin/Fourier projected spectrum on the bundled `3:1:1` ideal trefoil geometry. This is explicitly labelled **frozen/local**, not Floquet.
- **K6** performs a nonlinear relative-periodic-orbit search. A true relative-return monodromy is constructed **only if** the RPO closes. Otherwise K6 is `SKIP` with `NO_RPO__TRUE_FLOQUET_SCIENTIFICALLY_LOCKED`.

### Phase III — K7–K9: blind resonances and phase coherence

- **K7** enumerates non-trivial 4-wave and 6-wave candidates from the numerically obtained mode spectrum; the search does not assume that six-wave coupling must win.
- **K8** seeds the best numerical sextet in a full nonlinear regularized Biot–Savart ring evolution and measures combination-phase locking and energy exchange.
- **K9** computes normalized 6-wave pentacoherence, a 4-wave comparison, and a deliberately worse-detuned 6-wave control.

### Phase IV — K10–K14: broadband transfer and symmetry audit

- **K10** initializes a random-phase low-mode band and measures finite-time transfer into initially empty higher modes.
- **K11** reports a cumulative transfer-flux **proxy**; it is not promoted to a stationary inertial-range flux without forcing/dissipation closure.
- **K12** compares linear and nonlinear timescales over the finite simulation interval.
- **K13** evaluates four trefoil configurations: geometry/mirror × circulation sign.
- **K14** performs a source scan for numerical fine-structure targets. The blind modules contain no such benchmark target.

See `docs/THEORY_AND_GATES.md` for exact interpretation rules.

## Individual commands

```bat
run_phase1.cmd
run_phase2.cmd
run_phase3.cmd
run_phase4.cmd
```

Use `full` as the first argument for the higher-resolution preset, e.g.

```bat
run_phase3.cmd full
```

Python equivalents:

```bash
python run_all.py --preset quick --out-dir audit_out
python run_all.py --preset full  --out-dir audit_out_full
```

For a fallback-only diagnostic:

```bash
python run_all.py --preset quick --force-python --out-dir audit_out_python
```

The normal Windows `run_all.cmd` is intentionally stricter: it requires a working native C++ extension before running the scientific campaign.

## Main outputs

```text
audit_summary.json
phase1/K0_rankine_paper_benchmark.csv
phase1/K1_SST_core_model_scales.csv
phase1/K3_ring_amplitude_sweep.csv
phase2/K4_ring_linear_spectrum.csv
phase2/K5_trefoil_frozen_kelvin_spectrum.csv
phase2/K6_rpo_candidate.json
phase2/K6_true_monodromy.json          # only if the RPO gate opens
phase3/K7_four_wave_resonances.csv
phase3/K7_six_wave_resonances.csv
phase3/K8_K9_sextet_diagnostics.json
phase3/sextet_modal_timeseries.csv
phase4/broadband_modal_timeseries.csv
phase4/K12_timescale_separation.csv
phase4/K13_chirality_four_configurations.csv
```

## Gate semantics

- `PASS` — implemented numerical criterion passed.
- `WARN` — diagnostic is usable but the desired convergence/separation criterion was not reached.
- `DIAGNOSTIC` — intentionally descriptive; no pass/fail physical claim is made.
- `SKIP` — a prerequisite scientific gate is closed. This is **not** silently converted into a numerical success.
- `FAIL` — a hard numerical/scientific criterion failed; `run_all.py` exits with code 2.

Most importantly:

> **No accepted RPO → no true Floquet monodromy.**

## Core-model caveats

The workbench currently uses a regularized line-filament Biot–Savart kernel. Therefore:

- `eps` is a numerical finite-core closure scale, not automatically identical to a derived SST core profile;
- the trefoil spectrum is a centerline-model test;
- K8–K12 are nonlinear mode-transfer experiments, not a first-principles 3D Euler finite-core calculation;
- reconnection is not modeled and should never be inferred from this package;
- a future finite-core Euler/compact-support core implementation can replace the backend while keeping the same four-phase gates.

## Validation bundled with v0.1.1

The Python fallback quick campaign and unit tests were executed in the build environment. See `VALIDATION.md` and `reference_fallback_quick/`.

Native pybind11 compilation could not be executed in the artifact sandbox because that runtime does not contain pybind11 and has no network access. The native source is based on the already-used SST regularized Biot–Savart backend and the Windows setup script installs pybind11 before compiling. Native/Python parity is still a hard K2 gate when run normally.

## References

```latex
\begin{thebibliography}{99}

\bibitem{Barckicke2026KWT}
J.~Barckicke, C.~Gissinger, and E.~Falcon,
``Experimental evidence of Kelvin-wave turbulence along a vortex core,''
\textit{Physical Review Letters} (2026),
doi:10.1103/t3bt-m431,
\url{https://arxiv.org/abs/2607.07535}.

\bibitem{Thomson1880}
W.~Thomson,
``Vibrations of a columnar vortex,''
\textit{Philosophical Magazine} \textbf{10}, 155--168 (1880),
doi:10.1080/14786448008626912.

\bibitem{KozikSvistunov2004}
E.~Kozik and B.~Svistunov,
``Kelvin-Wave Cascade and Decay of Superfluid Turbulence,''
\textit{Physical Review Letters} \textbf{92}, 035301 (2004),
doi:10.1103/PhysRevLett.92.035301.

\bibitem{LvovNazarenko2010}
V.~S.~L'vov and S.~Nazarenko,
``Weak turbulence of Kelvin waves in superfluid He,''
\textit{Low Temperature Physics} \textbf{36}, 785--791 (2010),
doi:10.1063/1.3499242.

\bibitem{Floquet1883}
G.~Floquet,
``Sur les equations differentielles lineaires a coefficients periodiques,''
\textit{Annales scientifiques de l'Ecole Normale Superieure}, Serie 2,
\textbf{12}, 47--88 (1883),
doi:10.24033/asens.220.

\end{thebibliography}
```
