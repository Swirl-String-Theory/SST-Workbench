# SST Internal Chi-Phase Verification Package

Self-contained Research Track package for verifying the internal torsional phase mechanism
introduced in the SST Rosetta / Gauge-Sector Roadmap.

## Purpose

The package tests the local internal phase-sector identities

```math
\mathcal I_\chi=\rho_f\int_A r_\perp^2\,dA,
\qquad
\mathcal K_\chi=\rho_f v_{\circlearrowleft}^2\int_A r_\perp^2\,dA,
```

and therefore

```math
c_\chi^2=\frac{\mathcal K_\chi}{\mathcal I_\chi}=v_{\circlearrowleft}^2.
```

It also tests the horn-loop spectrum

```math
L_\chi=2\pi r_c
\quad\Rightarrow\quad
\omega_n=n\omega_c
```

in both continuous and finite-difference form.

## Files

- `sst_chi_phase.cpp` — pybind11 C++ kernel.
- `sst_chi_phase_build.py` — local auto-build helper.
- `simulate_chi_phase.py` — runner, CSV export, plots, and assertions.
- `README.md` — this file.

## Run

```bash
pip install numpy matplotlib pybind11 setuptools
python simulate_chi_phase.py
```

The script builds the C++ extension in-place if needed, then writes outputs to `./exports/`:

- `chi_phase_speed_sweep.csv`
- `chi_phase_speed_sweep.png`
- `chi_cross_section_moment_error.png`
- `chi_horn_loop_spectrum.csv`
- `chi_horn_loop_spectrum.png`

## Status

Research Track sanity test. Passing this package supports the internal
`chi -> U(1)_chi` phase-speed mechanism, but it does not by itself prove
`Q_chi -> Q_em`, electroweak mixing, non-abelian gauge sectors, or the SST mass spectrum.
