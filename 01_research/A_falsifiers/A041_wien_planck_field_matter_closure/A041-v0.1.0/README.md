
# Wien–Planck SST Field–Matter Closure Falsifier v0.1.0

This package contains two linked but logically separated tests:

1. **Provenance audit** of
   \[
   4\pi^2\rho_{\text{core}}\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}r_c^4 \simeq h.
   \]
2. **Blind Universal Action / Planck Gate**, which tests measured dynamical spacings
   \[
   \Delta E/f \stackrel{?}{=} h,\qquad
   \Delta E/\omega \stackrel{?}{=} \hbar
   \]
   without giving the blind analyzer access to \(h\), \(\hbar\), carrier family, mode labels,
   or seed identities.
3. **Wien–Planck field–matter closure gates** for Euler similarity, inertial/energy mass closure,
   pressure-monopole universality, and knot/fluid statistical equilibration.

## Critical provenance result

Under the legacy SST dependency chain

\[
\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}=\frac{\alpha c}{2},
\]

\[
F_{\text{swirl}}^{\max}
=\frac{\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}\hbar}{2r_c^2},
\]

\[
\rho_{\text{core}}
=\frac{4F_{\text{swirl}}^{\max}}{\pi\alpha^2c^2r_c^2},
\]

the relation is algebraically forced:

\[
4\pi^2\rho_{\text{core}}\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}r_c^4
=2\pi\hbar=h.
\]

Therefore the numerical agreement is **not an independent prediction** if those equations are the defining provenance of the canonical constants.

## Action-convention correction

The bare hydrodynamic combination

\[
J_c=\rho_{\text{core}}\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}r_c^4
\]

satisfies

\[
J_c=\frac{h}{4\pi^2}=\frac{\hbar}{2\pi}
\]

under that chain. It is therefore **not** itself the Planck action quantum.

A genuine Planck gate must measure the spectrum dynamically:

\[
\Delta E=h f=\hbar\omega.
\]

## Run everything

```bat
run_all.cmd
```

The supplied demos are synthetic pipeline controls only and are never SST evidence.

## Run on real action observations

Required CSV columns:

```text
carrier_id,family,mode_label,condition,profile,seed_name,frequency_Hz,omega_rad_s,delta_E_J
```

Then:

```bat
run_action_real.cmd path\to\observations.csv
```

The blind analyzer sees only opaque IDs and numerical observables.

## Run field–matter closure data

Required columns:

```text
scale_a,omega_rad_s,M_E_kg,M_I_kg,C_p,beta_knot,beta_fluid,energy_drift_rel
```

```bat
run_closure_real.cmd path\to\closure_observations.csv
```

See `docs\GATES.md` and `PROVENANCE_AUDIT.md`.
