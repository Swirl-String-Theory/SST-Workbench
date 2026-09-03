# Wien–Planck SST Field–Matter Closure Falsifier v0.2.2

## Strict anti-circularity correction

v0.2.2 changes the Universal Action / Planck branch from **target-blind with SST physical scaling**
to **SST-constant-blind and SI-blind discovery**.

The pre-reveal scientific path uses only

\[
L_{\rm hat}=1,\qquad
\Gamma_{\rm hat}=1,\qquad
a/L,\qquad
\text{dimensionless geometry and numerical controls}.
\]

It does **not** use the canonical values of

\[
r_c,\quad
\mathbf{v}_{\!\boldsymbol{\circlearrowleft}},\quad
\rho_{\!f},\quad
\rho_{\text{core}},\quad
F_{\text{swirl}}^{\max},\quad
F_{\text{gr}}^{\max},
\]

nor \(h\), \(\hbar\), \(\alpha\), \(c\), or an SI conversion scale.

The dimensionless line energy is

\[
\hat E
=
\frac{1}{8\pi}\hat S,
\]

where \(\hat S\) is the regularized line-energy double integral from the same
dimensionless geometry/kernel used by the dynamics.

The blind action observables are therefore

\[
\hat J_f
=
\frac{\Delta\hat E}{\hat f},
\qquad
\hat J_\omega
=
\frac{\Delta\hat E}{\hat\omega}.
\]

The blind result can establish only a:

\[
\boxed{\text{dimensionless universal-action candidate}}
\]

—not an absolute prediction of \(h\) or \(\hbar\).

## One-click strict blind run

```bat
run_all.cmd
```

Default dataset:

```text
..\..\KnotPlot\knots\final
```

The chain is

```text
environment
 -> native build
 -> self-test
 -> code seal
 -> blind constant/SI leakage guard
 -> dataset inventory
 -> dimensionless campaign
 -> blind identity quarantine
 -> blind dimensionless action analysis
 -> BLIND archive
```

`run_all.cmd` intentionally does **not** execute the provenance audit and does
**not** perform an SI/Planck reveal.

Read `REPORT_BLIND.md` first.

## Manual reveal

Without an independent SI scale:

```bat
run_40_reveal.cmd outputs\basic_YYYYMMDD_HHMMSS
```

This reveals identities and reports the dimensionless candidate, but the
absolute Planck gate remains

```text
INDETERMINATE_NO_INDEPENDENT_SI_NORMALIZATION
```

With a genuinely independent SI normalization:

```bat
run_40_reveal.cmd outputs\basic_YYYYMMDD_HHMMSS reveal_only\my_independent_scale.json
```

The file must contain

```json
{
  "rho_kg_m3": 0.0,
  "Gamma_m2_s": 0.0,
  "L_m": 0.0,
  "independent_of_Planck_chain": true,
  "provenance_note": "How each scale was determined independently."
}
```

The dimensional action scale is then

\[
J_0=\rho\Gamma L^3.
\]

Because

\[
E_0=\rho\Gamma^2L,\qquad
f_0=\frac{\Gamma}{L^2},
\]

one has

\[
\frac{\Delta E}{f}
=
J_0\frac{\Delta\hat E}{\hat f}.
\]

Only if the scale provenance is independent may the reveal compare

\[
J_0\hat J_f\stackrel{?}{=}h
\]

and

\[
J_0\hat J_\omega\stackrel{?}{=}\hbar.
\]

## Legacy SST normalization is a negative control, not a prediction

The reveal-only file

```text
reveal_only\legacy_sst_normalization_CONTAMINATED.json
```

uses

\[
\rho=\rho_{\text{core}},\qquad
\Gamma=2\pi r_c\mathbf{v}_{\!\boldsymbol{\circlearrowleft}},\qquad
L=r_c.
\]

Then

\[
J_0
=
\rho_{\text{core}}\Gamma r_c^3
=
2\pi\rho_{\text{core}}
\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}r_c^4
\simeq\hbar.
\]

The provenance audit shows this is algebraically inherited from the legacy
Planck-containing parameter chain. The reveal therefore classifies it as
`CONTAMINATED_OR_UNPROVEN_NORMALIZATION` and cannot issue an independent
absolute Planck PASS.

## Reveal-only provenance audit

After the blind result is frozen:

```bat
run_90_provenance_audit_REVEAL_ONLY.cmd
```

`run_05_provenance.cmd` now deliberately exits with an error so that provenance
material is never automatically mixed into the blind chain.

## Main blind gates

- `UA0_no_SST_SI_target_leak`
- `UA1_omega_equals_2pi_f`
- `UA2_recurrent_mode_prerequisite`
- `UA2b_relative_equilibrium`
- `UA2c_positive_resolved_dimensionless_energy`
- `UA3_mesh_quality`
- `UA3b_temporal_convergence`
- `UA4_reject_classical_continuous_action`
- `UA5_dimensionless_action_amplitude_independence`
- `UA6_dimensionless_action_universality`
- `UA7_spatial_convergence`

A discrete mode spectrum by itself is not evidence for quantized action.

## Epistemic scope

This remains a regularized vortex-centerline falsifier. It does not by itself:
- certify input topology;
- solve a full 3-D finite-core Euler core;
- prove thermodynamic equilibration;
- establish an absolute Planck scale without independent dimensional provenance.

See `docs/THEORY_AND_GATES.md`,
`docs/STRICT_BLINDNESS_v0.2.2.md`,
`PROVENANCE_AUDIT.md`, and `VALIDATION.md`.


## Windows build note — v0.2.2

The v0.2.1 user run reached Visual Studio 2026 environment discovery but failed before C++ compilation because setuptools spawned a contaminated `cmd /u /c vcvarsall...` bootstrap shell. v0.2.2 bypasses that bootstrap.

Recommended first native retry:

```bat
run_01_build_native_clean.cmd
```

Then run the scientific chain, preferably with an explicit dataset path:

```bat
run_all.cmd "C:\workspace\projects\SST-Workbench\KnotPlot\knots\final"
```

See `docs\WINDOWS_BUILD_FIX_v0.2.2.md`.
