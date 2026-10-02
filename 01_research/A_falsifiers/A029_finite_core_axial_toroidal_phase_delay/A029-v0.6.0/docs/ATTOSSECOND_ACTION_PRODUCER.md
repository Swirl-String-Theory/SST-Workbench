# A029-v0.5.0 — Phase-delay → specific-action producer

## Purpose

A029 already contains finite-core eigenmodes, intrinsic/advection frequency separation, loop closure, chirality, holonomy and independent-return phase machinery. Those quantities are valuable, but most are currently expressed in the model's normalized variables. v0.5.0 adds a strict bridge toward a physical action without pretending that a normalized loop phase is already an attosecond observable.

## The new derived route

If an SST calculation supplies a physical **mass-specific Lagrangian difference**

\[
\delta\ell(t)
\quad [\delta\ell]=\mathrm{m^2\,s^{-2}},
\]

then A029 may derive

\[
\boxed{
\delta s(t)=\int_{t_0}^{t}\delta\ell(t')\,dt'
}
\]

with

\[
[\delta s]=\mathrm{m^2\,s^{-1}}.
\]

For a material parcel moving in a **prescribed** incompressible-Euler pressure field, v0.5.0 also exposes the effective diagnostic

\[
\ell_{\rm eff}=\frac12|\mathbf v|^2-\frac{p}{\rho_{\!f}},
\]

so that a candidate-minus-reference trajectory can provide

\[
\delta\ell_{\rm eff}
=\frac12\left(|\mathbf v_1|^2-|\mathbf v_0|^2\right)
-\frac{p_1-p_0}{\rho_{\!f}}.
\]

Every term has units \(\mathrm{m^2\,s^{-2}}\). This is a **trajectory-level effective action diagnostic**, not a claim that \(\tfrac12v^2-p/\rho_{\!f}\) is the complete constrained Euler-field action. The upstream solver must still supply self-consistent pressure and enforce incompressibility. The further identification of this mechanical action difference with a quantum phase remains the SST bridge hypothesis.

This is exactly the input type required by the target-blind A042-v0.3.0 bridge:

\[
\delta\phi=\frac{\delta s}{(\hbar/m)_{\rm QGI}}.
\]

## What v0.5.0 explicitly refuses

The existing fields

- `loop_phase`,
- `phi_target_independent`,
- `omega_median`,
- `omega_intrinsic_median`,
- normalized `tau_return`,
- holonomy by itself,

are **not** converted into SI action. Doing that without a physical scale/action functional would be dimensional relabeling, not a derivation.

A stationary-channel relation

\[
\delta s=-\varepsilon\,\delta t
\]

is dimensionally valid when \(\varepsilon\) is specific energy, but remains `CONDITIONAL_SPECIFIC_ACTION` unless the contract independently certifies that this relation was derived for the SST channel being exported.

## New gates

- `A29A1_PHYSICAL_SCALE_PROVENANCE`
- `A29A2_SPECIFIC_ACTION_DIMENSIONAL_CLOSURE`
- `A29A3_MODAL_PHASE_NONPROMOTION`
- `A29A4_RELATIVE_ACTION_STRUCTURE`
- `A29A5_EXPORT_SEAL`

## Remaining bridge gap

A029 can now produce a qualified \(\delta s\) field, but it does **not** know the photoionization kernel coordinates \((E,\theta,\tau,t)\). The map from finite-core SST mode/trajectory coordinates into that orthodox kernel must be separately derived and frozen. Until then, A042 correctly rejects the A029 provenance field because `mapping_to_attosecond_kernel` remains `NOT_YET_SUPPLIED_BY_A029`.

This is intentional: it keeps the first three upgrades connected without smuggling the fourth, experimental falsifier, in through an arbitrary fit.
