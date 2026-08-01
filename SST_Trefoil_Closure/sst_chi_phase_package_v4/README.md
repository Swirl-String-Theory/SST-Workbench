# SST chi-phase package v4 — four-profile core admissibility selector

v1/v2 should be treated as archived shared-moment consistency checks. v3 broke the tautology by extracting the torsional stiffness from a radial core profile. v4 adds an explicit four-profile admissibility test.

## Research status

**Research Track / numerical admissibility selector.** This package does not prove \(Q_\chi \to Q_{\rm em}\), does not derive non-abelian gauge structure, and does not canonize a universal \(c_\chi=v_{\rm swirl}\) law.

It tests the non-tautological stiffness relation

\[
I_\chi=\rho_f\int_A r_\perp^2\,dA,
\]

\[
K_\chi=\rho_f\int_A v_\theta(r)^2 r_\perp^2\,dA,
\]

\[
c_\chi^2=\frac{K_\chi}{I_\chi}
=\frac{\int_A v_\theta(r)^2 r_\perp^2\,dA}{\int_A r_\perp^2\,dA}.
\]

Therefore \(c_\chi=v_{\rm swirl}\) holds only if the profile's \(r_\perp^2\)-weighted RMS speed equals \(v_{\rm swirl}\). It is not forced in v4.

## Default four profiles

The default run tests exactly four candidate profiles:

1. `uniform` with boundary normalization.
2. `solid_body` with boundary normalization.
3. `irrotational_reg` with boundary normalization and `eps=0.05`.
4. `gaussian_core` with max normalization and `sigma=0.35`.

The package reports:

- \(c_\chi/v_{ref}\)
- \(\Gamma(a)/(2\pi a v_{ref})\)
- \(E_{kin}/L\)
- center-axis regularity: \(v_\theta(0)=0\)
- boundary circulation matching: \(v_\theta(a)=v_{ref}\)
- exterior \(1/r\) slope matching: \(a v_\theta'(a)/v_\theta(a)\approx -1\)
- finite-energy diagnostic
- finite-difference spectrum convergence control

## Run

```powershell
cd path\to\sst_chi_phase_package_v4
python simulate_chi_phase_v4.py
```

Force pure Python:

```powershell
python simulate_chi_phase_v4.py --python
```

Force C++ rebuild:

```powershell
python sst_chi_phase_v4_build.py --force
```

Extended run with Rankine and calibration references:

```powershell
python simulate_chi_phase_v4.py --extended
```

## Outputs

All outputs go to `exports/`:

- `chi_v4_profile_admissibility.csv`
- `chi_v4_profiles.png`
- `chi_v4_profile_speed_ratio.png`
- `chi_v4_energy_per_length_ratio.png`
- `chi_v4_boundary_circulation.png`
- `chi_v4_admissibility_matrix.png`
- `chi_v4_profile_spectrum.csv`
- `chi_v4_profile_spectrum.png`
- `chi_v4_spectrum_convergence.csv`
- `chi_v4_spectrum_convergence.png`
- `chi_v4_run_results_summary.txt`

## Canon interpretation

v4 is designed to prevent tautological canonization. The safe statement is:

\[
c_\chi^2=\left\langle v_\theta^2\right\rangle_{r_\perp^2}
\]

with

\[
\left\langle v_\theta^2\right\rangle_{r_\perp^2}
=\frac{\int_A v_\theta(r)^2 r_\perp^2\,dA}{\int_A r_\perp^2\,dA}.
\]

Only after SST independently selects an admissible core profile, or defines \(v_{\rm swirl}\) as this weighted RMS speed, may \(c_\chi=v_{\rm swirl}\) be promoted from conditional closure to a stronger physical statement.
