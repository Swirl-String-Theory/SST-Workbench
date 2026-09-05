# Kelvin--M'Farlane Central-Hole Dynamical Gate

## Falsifiable question

\[
\boxed{\text{Is the central threaded hole a robust dynamical structure, or only a visual gap in centerline geometry?}}
\]

The falsifier separates three notions that must not be conflated:

\[
\mathcal C=\text{core centerline topology},
\qquad
\mathcal A=\text{co-moving carried-fluid/atmosphere topology},
\qquad
\mathcal F=\text{through-flow topology}.
\]

A hole in \(\mathcal C\) is not sufficient evidence for a hole in \(\mathcal A\) or \(\mathcal F\).

## 1. Co-moving velocity

The carrier velocity is fit to the best normal-plane rigid motion,

\[
\mathbf v_i\simeq
\mathbf U+\boldsymbol\Omega\times(\mathbf x_i-\mathbf c),
\]

with tangential marker sliding quotient out. The sampling field is then

\[
\mathbf u_{\rm rel}(\mathbf x)
=
\mathbf u(\mathbf x)-\mathbf U-
\boldsymbol\Omega\times(\mathbf x-\mathbf c).
\]

This is essential: a stationary Lagrangian structure of a translating/rotating vortex must be sought in the carrier frame, not in the laboratory frame.

## 2. Blind geometric axis

The central axis is estimated from the anonymous carrier centerline only. Deterministic Fibonacci-sphere directions through the carrier centroid are ranked by a low quantile of perpendicular centerline clearance. No private knot label, hand-entered hole axis or active/null identity is used.

## 3. Frozen Lagrangian / streamline transport

For the frozen co-moving field the material trajectory curves are reparameterized by arclength,

\[
\frac{d\mathbf x}{ds}=\frac{\mathbf u_{\rm rel}}{|\mathbf u_{\rm rel}|},
\]

away from stagnation. This does not change streamline connectivity, but prevents a slow open channel from being called ``captured'' simply because a finite physical-time window was too short. Near-stagnation behavior is handled separately by the axial stagnation/pinch diagnostics.

Two deterministic seed families are used.

### Upstream disk

Seeds begin on the inferred upstream side of the passage. A through-channel fraction is

\[
f_{\rm through}=\frac{N_{\rm downstream\ crossing}}{N_{\rm seeds}}.
\]

Lateral escape is tracked separately.

### Mid-plane disk

Central seeds test a carried/captured atmosphere:

\[
f_{\rm resident}=\frac{N_{\rm still\ resident}}{N_{\rm seeds}}.
\]

The frozen class is therefore based on actual trajectories, not on centerline clearance.

## 4. Stagnation scan

Along the inferred axis,

\[
u_{\parallel}(s)=
\mathbf u_{\rm rel}(\mathbf c+s\hat{\mathbf n})\cdot\hat{\mathbf n}
\]

is sampled for sign changes. This supplies a diagnostic proxy for Kelvin-like stagnation/separatrix transitions.

For sufficiently translation-dominated cases the code also reports

\[
\chi_{\rm hole}=\frac{u_{\parallel,\rm induced}(0)}{U_{\parallel}},
\]

but this is explicitly marked **generic**. It may be interpreted as Kelvin's \(u_c/U\) order parameter only when a single coherent translation axis exists.

## 5. Finite-evolution persistence

The complete anonymous filament state is evolved with the regularized Biot--Savart/LIA model. After the preregistered horizon, the final carrier is rigidly aligned back to the initial reference and the complete frozen Lagrangian test is repeated.

Required observables include

\[
R_c=\frac{c_{\rm hole,final}}{c_{\rm hole,initial}},
\]

and class persistence

\[
I_{\rm class}=\mathbf 1(C_{\rm final}=C_{\rm initial}).
\]

## 6. Perturbation persistence

A deterministic normal deformation basis is built from low Fourier modes. For every preregistered mode \(q_j\), both signs are tested:

\[
\mathbf X_{j,\pm}
=
\mathbf X_0\pm\epsilon q_j.
\]

No favorable sign is selected after inspection. The package reports both same-class fraction and robust-class fraction.

## 7. Blind active/null control

The active and null candidates contain identical carrier and closed-thread centerlines. The null has

\[
\Gamma_{\rm thread}=0,
\]

while the active candidate has hidden non-zero thread circulation.

Hence the pair directly controls the hypothesis

\[
\text{``the hole only looks present because the centerlines have a gap.''}
\]

## 8. Verdicts

Candidate-level:

- `ROBUST_OPEN_THREADED_CHANNEL`
- `ROBUST_CAPTURED_VORTEX_ATMOSPHERE`
- `CRITICAL_OR_TOPOLOGY_SWITCHING`
- `VISUAL_HOLE_NOT_DYNAMICALLY_ESTABLISHED`

A `ROBUST_*` verdict requires both robust-class and **same-class** perturbation fractions to pass. Switching from open-channel to captured-atmosphere under perturbation is not counted as a robust open channel.

Post-seal inference is explicitly two-layered.

**Existence status** answers whether the hole is dynamical at all, including:

- `VISUAL_HOLE_ONLY_WITHIN_TESTED_MODEL_AND_HORIZON`
- `DYNAMICAL_HOLE_DETECTED_IN_ACTIVE_THREAD_ARM`
- `DYNAMICAL_HOLE_DETECTED_ALSO_IN_ZERO_CIRCULATION_CONTROL`
- `DYNAMICAL_HOLE_DETECTED_WITH_MIXED_CARRIER_DEPENDENCE`

**Causal thread-circulation status** is separate:

- `SUPPORTS_THREAD_CIRCULATION_STABILIZES_DYNAMICAL_HOLE`
- `FALSIFIES_THREAD_CIRCULATION_AS_HOLE_STABILIZER`
- `INDETERMINATE_THREAD_CIRCULATION_CAUSAL_EFFECT`

The causal carrier vote is obtained from the anonymous multi-cost decision **sealed before reveal**. The reveal does not choose a favorable cost component after identities are known. Repeated \(\beta\), pitch or circulation strata are carrier-clustered and do not count as independent knots.

## 9. Failure modes that remain falsifying

The package does not rescue a candidate when:

- the geometric hole collapses;
- the field is laterally incoherent;
- tracers neither transit nor remain captured;
- the class changes during finite evolution;
- perturbations destroy the class;
- the filament trajectory hits the preregistered contact gate;
- the analytic Kelvin oracle fails.

## 10. Scope

The result is conditional on the regularized filament approximation. A positive result should be followed by a higher-fidelity Euler/VortexLab calculation with volumetric vorticity and invariant-manifold extraction. A negative result is already useful: the centerline gap alone is not a dynamical mechanism.
