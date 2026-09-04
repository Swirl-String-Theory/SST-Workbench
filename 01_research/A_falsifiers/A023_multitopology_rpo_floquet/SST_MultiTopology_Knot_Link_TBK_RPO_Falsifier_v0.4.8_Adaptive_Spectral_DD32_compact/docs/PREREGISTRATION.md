# v0.3.0 preregistration — Coupled Torsion–Breathing–Kelvin Balance + RPO/Floquet

## Hypothesis

The v0.2 result established a distinction between local cross-lobe separation and global reduced instability. v0.3.0 tests the stronger alternative hypothesis:

> A trefoil may require a phase-coherent dynamical balance among breathing, torsion-sensitive and Kelvin-like centerline modes. If such a balance exists, removing the relevant inter-family coupling should worsen stability, and a nonlinear relative-periodic recurrence may possess a bounded reduced Floquet return map.

No threshold is tuned after source unblinding.

## Blinding

The Fremlin and KnotPlot source identities are converted to `B01/B02` before the analysis. Blind input hashes, analyses, scores, nulls and the blind campaign verdict are written before `unblind_manifest.json`.

## Legacy decision rule

The critical gates remain exactly:

- `G0_numerical_sanity`
- `G2_reduced_stability`
- `G3_cross_lobe_stabilizes`
- `G4_nearest_pair_cross_separates`
- `G6_ringdown_bounded`

`G1`, `G5`, and `G7`–`G19` are diagnostic. Thus v0.3.0 cannot obtain an overall PASS by weakening the historical criteria.

## Expanded basis

A discrete tangent/normal/binormal frame is constructed on a uniform arclength centerline. The existing six tilt/breathing modes are augmented with three lobe-windowed binormal torsion-sensitive perturbations and normal/binormal Fourier modes

\[
\cos(ks)\mathbf n,\quad \sin(ks)\mathbf n,\quad
\cos(ks)\mathbf b,\quad \sin(ks)\mathbf b.
\]

All modes are projected normal to the filament, stripped of rigid motion, Gram–Schmidt orthogonalized and RMS normalized.

BASIC Kelvin harmonics: `k = 2,3,4`.

EXTENDED Kelvin harmonics: `k = 2,3,4,5,6`.

## Expanded Jacobian convergence

Symmetric finite differences are evaluated at the configured `coupled_eps_values`. The maximum relative matrix change is

\[
C_J=\max_i
\frac{\|J(\epsilon_i)-J(\epsilon_{i+1})\|_F}
{\max(\|J(\epsilon_i)\|_F,\|J(\epsilon_{i+1})\|_F)}.
\]

`G12` requires both mixed TBK participation and the preregistered convergence bound.

## Family coupling ablations

For each family, all off-diagonal entries connecting that family to other families are removed while within-family blocks are retained. The growth penalty is

\[
\Delta g_f=
\frac{g(J_{\rm decouple\,f})-g(J)}{\rho(J)},
\qquad
g(A)=\max\Re\operatorname{eig}(A).
\]

A positive \(\Delta g_f\) means the removed coupling had a stabilizing effect in the reduced model.

A second counterfactual retains only family-diagonal blocks. `G16` asks whether the full inter-family coupling improves the worst resolved growth rate by the preregistered margin.

## Mixed oscillatory-mode selection

For every expanded eigenvector the energy-like coefficient participation in tilt, breathing, torsion and Kelvin families is reported. An oscillatory mode is scored for simultaneous TBK participation and nonzero imaginary frequency. `G12` requires a minimum participation in each of B/T/K.

## RPO phase scan

The real and imaginary parts of the selected complex eigenvector define an initial phase family

\[
\delta X_\phi=
A\left[\cos\phi\,\Re\Phi-\sin\phi\,\Im\Phi\right].
\]

For each phase the full nonlinear finite-core Biot–Savart shape dynamics is integrated without reconnection or repulsion logic.

A valid candidate requires:

\[
R_{\rm excursion}\ge R_{\rm excursion}^{\min},
\]

followed by

\[
R(T)\le R_{\max},
\qquad
\frac{R(T)}{\max_{0<t<T}R(t)}\le\eta_{\max},
\]

with no near-core event. This explicit excursion-return requirement rejects monotonic slow drift.

## Phase lock

For a valid candidate only, the dominant breathing, torsion and Kelvin projected coordinates are analyzed in multiple windows. `G17` requires both:

- relative dominant-frequency spread below the configured maximum;
- mean circular resultant of pairwise phase differences above the configured minimum.

## Floquet gate

`G19` is conditional. No acceptable RPO means no scientific Floquet claim.

For a valid recurrence, the nonlinear return map is finite-differenced in a deterministic reduced subspace. If any reference or perturbed return reaches the near-core threshold, the Floquet result is invalidated.

The multipliers

\[
\mu_i=\operatorname{eig}M(T)
\]

are reported. One multiplier nearest unity is treated as the candidate neutral phase multiplier; the diagnostic bound is applied to the remaining multipliers.

## v0.3.0 diagnostic gates

### G12 — mixed TBK mode resolved
Requires minimum B/T/K participation and expanded-Jacobian convergence.

### G13 — torsion coupling stabilizes
Requires positive growth penalty after torsion decoupling.

### G14 — Kelvin coupling stabilizes
Requires positive growth penalty after Kelvin decoupling.

### G15 — breathing coupling stabilizes
Requires positive growth penalty after breathing decoupling.

### G16 — collective TBK/inter-family coupling stabilizes
Requires the fully coupled matrix to outperform the family-block-diagonal counterfactual.

### G17 — TBK phase lock
Requires a valid RPO candidate, frequency agreement and stable pairwise phase differences.

### G18 — RPO recurrence
Requires excursion, return, return-ratio and no-core-event conditions.

### G19 — Floquet bounded
Requires a valid G18-like recurrence and bounded projected non-neutral return-map multipliers.

## Scope limitations

- The torsion modes perturb centerline geometry; they do not model an independent internal twist field of a finite-radius tube.
- Kelvin-like Fourier modes are a finite basis, not a complete spectrum.
- Family ablations are reduced-matrix interventions, not modifications of the physical Euler equation.
- A passing projected Floquet gate is evidence for reduced stability only; it is not a proof of full three-dimensional Euler stability.
