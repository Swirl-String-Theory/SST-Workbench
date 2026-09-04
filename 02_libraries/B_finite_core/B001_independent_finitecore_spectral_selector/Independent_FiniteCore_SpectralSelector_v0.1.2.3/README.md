# Independent Finite-Core Spectral Selector v0.1.2.3

A blind, dimensionless numerical falsification package for asking whether a finite-core periodic vortex ring possesses a robust internally selected spectral scale.

## Scientific boundary

This package does **not** contain external physical constants, external target values, or target matching. Length and circulation are internal numerical units only:

- core radius unit: `a = 1`
- circulation unit: `Gamma = 1`
- scanned scale: `q = ln(L/a)`

v0.1.2.3 does not attempt to interpret an accepted numerical feature in any external physical model. That comparison belongs after result freezing.

## Why v0.1.2.3 exists

v0.1.1 found that global eigenvalue minima could be stable against finite-difference step and image-shell depth while migrating with node resolution. The remaining ambiguity was branch identity: a globally sorted eigenvalue at one resolution need not represent the same physical perturbation at another resolution.

v0.1.2.3 retains the v0.1.2 Fourier/C4 analysis and replaces global branch labels as the promotion authority with a Fourier/C4-resolved analysis.

For a ring sampled at angles `theta_j`, perturbations are projected on

`exp(i m theta_j)`, with signed modes `m = -M,...,+M`.

The periodic cubic image lattice is invariant under quarter-turns about the ring axis, not under arbitrary continuous rotations. Therefore the authoritative sectors are `m mod 4`, and coupling between `m` and `m +/- 4, +/- 8, ...` is allowed. The code explicitly measures:

- low-mode projection leakage;
- C4 symmetry leakage;
- per-sector eigenvalues;
- branch overlap across q;
- dominant signed m and dominant |m| weight;
- mode participation entropy.

A single 2x2 Fourier block is never assumed exact when sector mixing is present.

## Performance changes in v0.1.2.3

v0.1.2.3 adds performance improvements without relaxing the full/research convergence protocol:

- backend loading/build checks are cached per scan;
- the q-independent shell-0 self Jacobian is computed once per numerical case;
- `run_quick.cmd` now uses a true smoke baseline (`N=32/48`, `dq=0.05`, `max_m=8`);
- quick runs may use exact C4 Jacobian-column reconstruction with an independent rotated-column audit;
- `run_full.cmd` keeps the brute-force interaction Jacobian by default so research results remain directly comparable to v0.1.2.1.

For a less aggressive diagnostic use `run_quick_research.cmd` (`dq=0.025`, `max_m=12`). See `PERFORMANCE.md`.

## Primary promotion logic

Global-spectrum diagnostics remain in the output only as a reference. They **cannot promote a candidate** in v0.1.2.

A Fourier candidate is eligible only when:

1. the relative-equilibrium residual passes;
2. low-mode projection leakage is below the preregistered threshold;
3. C4 symmetry leakage is below the preregistered threshold;
4. the tracked branch overlap is sufficient;
5. the eigenvector has a sufficiently dominant |m| label;
6. `|m| >= 2`, excluding rigid-like low harmonics from candidate promotion.

A numerical candidate is promoted only if the same candidate kind, C4 sector, and dominant `|m|` converge across:

- resolution: `N = 48, 64, 96, 128`;
- high-resolution gate: `|q_96 - q_128| <= 0.010`;
- triplet gate: `N=64,96,128` occupy one `0.015` q-cluster;
- image shells: `S=2,3` agree within `0.010`;
- finite-difference steps: at least three values agree within `0.010`.

## Default full campaign

The default full scan is deliberately narrower than v0.1.1 because the previous *internal blind run* showed that the informative full-spectrum structure is confined to the near-cell regime. This narrowing uses no external physical target.

- `q = 2.31 ... 3.10`
- `dq = 0.01`
- `max_m = 12`
- C4 symmetry sectors
- baseline `N=96`, image shell 2, `h/a=1e-4`
- resolution ladder `48,64,96,128`
- shell ladder `1,2,3`
- FD ladder `3e-4,1e-4,3e-5`

## Windows workflow

```bat
run_native_preflight.cmd
run_all_checks.cmd --threads 16
run_quick.cmd
```

If those pass:

```bat
run_full.cmd
```

The full campaign writes `audit_fourier_convergence/` containing at least:

- `independence_manifest.json`
- `case_resolution_N48.json`
- `case_resolution_N64.json`
- `case_resolution_N96.json`
- `case_resolution_N128.json`
- `case_image_shell_S1.json`
- `case_image_shell_S2.json`
- `case_image_shell_S3.json`
- `case_fd_eps_H3e-4.json`
- `case_fd_eps_H1e-4.json`
- `case_fd_eps_H3e-5.json`
- `fourier_sector_rows.csv`
- `global_reference_rows.csv`
- `candidate_clusters.json`
- `audit_summary.json`

Freeze before any external comparison:

```bat
python freeze_results.py audit_fourier_convergence
```

## Useful commands

Fast smoke campaign:

```bat
run_quick.cmd
```

Higher-detail quick campaign:

```bat
run_quick_research.cmd
```

Single Fourier diagnostic probe:

```bat
run_fourier_probe.cmd
```

Full campaign with explicit native rebuild:

```bat
python run_fourier_convergence_campaign.py --force-build --build-verbose --threads 16 --out-dir audit_fourier_convergence
```

Python fallback, intended for validation rather than speed:

```bat
python run_fourier_convergence_campaign.py --quick --force-python --threads 1 --out-dir audit_fourier_python
```

## Output interpretation

`n_promoted_converged_candidates = 0` is a valid and important negative result. It means no Fourier/C4-resolved spectral selector passed the preregistered numerical convergence gates within the tested model class.

A promoted candidate is **not** a physical discovery. It means only that the dimensionless numerical feature survived the declared numerical gates and may then be frozen and compared externally.

## Native backend

The C++/pybind kernel computes the finite-core periodic Biot-Savart Jacobian. v0.1.2.3 adds an optional quick-only C4 column-reconstruction kernel while retaining the original brute-force kernel for full research runs. `requirements.txt` intentionally includes `setuptools`, `pybind11`, and `numpy`.

## Windows native runtime

v0.1.2.3 resolves the MinGW/Strawberry runtime DLL directories before `_native` is imported. `run_native_preflight.cmd` is authoritative: it builds the `.pyd` and then performs a strict import test. If that test fails, run `run_native_diagnostics.cmd`; it reports the compiler path, active DLL directories and locations of common MinGW runtime DLLs. No manual PATH edit should normally be required.

