# Theory and gates — v0.2.2

## Dimensionless vortex dynamics

The blind dynamics use

\[
L=1,\qquad \Gamma=1,
\]

with finite-core regularization represented only by the dimensionless ratio

\[
\epsilon_c = a/L.
\]

The centerline equation is integrated by RK4 with a resolution-aware timestep
proportional to \((\Delta s)^2\), fixed dimensionless final time, deterministic
subcycling, and scheduled arclength redistribution.

## Dimensionless energy

The regularized line diagnostic is

\[
\hat E
=
\frac{1}{8\pi}
\sum_{ij}
\frac{
\Delta\boldsymbol{\ell}_i\cdot\Delta\boldsymbol{\ell}_j
}{
\sqrt{|\mathbf m_i-\mathbf m_j|^2+\epsilon_c^2}
}.
\]

Only differences

\[
\Delta\hat E
=
\frac{\hat E_+ + \hat E_-}{2}-\hat E_0
\]

are used in the matched \(+\epsilon/-\epsilon\) action probe.

## Relative-equilibrium prerequisite

A geometric relaxation is not automatically a dynamical equilibrium. The
instantaneous velocity is fitted to

\[
\mathbf F_i
\approx
\mathbf U+\boldsymbol\Omega\times\mathbf X_i,
\]

with normalized residual

\[
\epsilon_{\rm RE}
=
\frac{
\|\mathbf F-(\mathbf U+\boldsymbol\Omega\times\mathbf X)\|_w
}{
\|\mathbf F\|_w
}.
\]

## Frozen discovery / holdout modes

The first configured fraction of the odd matched response is used to discover a POD
mode. The spatial mode is frozen. Frequency and recurrence diagnostics are then
evaluated on the holdout interval.

## Universal-action observables

\[
\hat J_f=\frac{\Delta\hat E}{\hat f},
\qquad
\hat J_\omega=\frac{\Delta\hat E}{\hat\omega}.
\]

The blind scorer has no absolute target.

## Blind gates

### UA0
No SST canonical value, SI action scale, or absolute target may enter the blind
campaign/config/input.

### UA1
\[
\hat\omega=2\pi\hat f.
\]

### UA2
A recurrent holdout mode must exist with configured minimum cycles, spectral
concentration and harmonic fit.

### UA2b
Relative-equilibrium admissibility.

### UA2c
\[
\Delta\hat E>0
\]
and resolved relative to the base energy.

### UA3
Mesh-quality bounds.

### UA3b
Temporal refinement at fixed dimensionless \(T_{\rm final}\).

### UA4
Reject the smooth classical continuity null when

\[
\hat J_f\propto A^{p_A}
\]

shows a well-resolved positive classical-like slope.

### UA5
A candidate universal action must be approximately amplitude independent:

\[
|p_A|\ll1.
\]

### UA6
Cross-carrier/resolution coefficient of variation of \(\hat J_f\) must pass.

### UA7
Highest-resolution medians must converge.

## Reveal dimensionalization

Given genuinely independent reveal-only scales,

\[
E_{\rm phys}
=
\rho\Gamma^2 L\,\hat E,
\qquad
f_{\rm phys}
=
\frac{\Gamma}{L^2}\hat f.
\]

Therefore

\[
\frac{\Delta E_{\rm phys}}{f_{\rm phys}}
=
\rho\Gamma L^3
\frac{\Delta\hat E}{\hat f}.
\]

Define

\[
J_0=\rho\Gamma L^3.
\]

Only after provenance certification of \(J_0\) may one compare the revealed
physical action with \(h\) or \(\hbar\).

## Floquet restriction

No accepted relative-periodic orbit implies no true Floquet monodromy. The current
POD/FFT mode extraction is not called a Floquet spectrum.
