# SST chi-phase package v5 — profile zoo / admissibility selector

This package tests candidate SST/Euler/NLSE core profiles for the internal torsional chi-phase speed.

v1/v2 are archive material: they checked the arithmetic of the shared-moment ansatz and therefore made `c_chi=v_swirl` tautological.

v5 uses the non-tautological profile-derived formula:

\[
\frac{c_\chi^2}{v_{\rm ref}^2}
=
\frac{\int_0^1 \rho_{\rm rel}(x)f(x)^2x^3\,dx}
{\int_0^1 \rho_{\rm rel}(x)x^3\,dx},
\]

where \(x=r/a\), \(v_\theta(r)=v_{\rm ref}f(x)\), and \(\rho_{\rm rel}(x)\) is an optional density depletion profile.

## Default profile families

1. `uniform_boundary`: constant tangential speed. Gives `c/v=1`, but axis vector field is not regular.
2. `solid_body_boundary`: Rankine/Euler core, `f=x`; regular core; expected `sqrt(2/3)`.
3. `smooth_matched_poly`: regular polynomial with `f(0)=0`, `f(1)=1`, `f'(1)=-1`; default `f=2x-x^3`.
4. `regularized_inv_r_boundary`: exterior-like `1/r` surrogate.
5. `lamb_oseen_boundary`: smooth Lamb-Oseen-like spread circulation.
6. `nlse_tanh_density_phase`: phase-vortex `1/r` velocity with tanh density depletion.
7. `nlse_pade_density_phase`: phase-vortex `1/r` velocity with Pade density depletion.
8. `gaussian_core_max`: peak-normalized central Gaussian swirl.
9. `gaussian_shell`: shell-like swirl concentration.

## Diagnostics

Each profile receives a 4-point screening score:

- axis velocity regularity: regular azimuthal vector field has `v_theta(0)=0`;
- boundary circulation match: `v_theta(a)=v_ref`;
- exterior slope match: `a v_theta'(a)/v_theta(a)≈-1`;
- finite weighted energy/stiffness.

This score is a screening tool, not a final physical proof.

## Run

```powershell
python simulate_chi_phase_v5.py
```

Force pure Python:

```powershell
python simulate_chi_phase_v5.py --python
```

Run broader parameter sweep:

```powershell
python simulate_chi_phase_v5.py --sweep
```

Force C++ rebuild:

```powershell
python sst_chi_phase_v5_build.py --force
```

## Canon-safe interpretation

The safe Research Track statement is:

\[
c_\chi^2
=
\left\langle v_\theta^2\right\rangle_{r^2,\rho}
=
\frac{\int_A \rho(r)v_\theta(r)^2r_\perp^2\,dA}
{\int_A \rho(r)r_\perp^2\,dA}.
\]

Then `c_chi=v_swirl` holds only if `v_swirl` is defined as this weighted RMS speed, or if SST core dynamics independently selects a profile whose weighted RMS equals the canonical speed.
