# Theory and gates — v0.4.0

## 1. Dimensionless centerline dynamics

The blind dynamics use

\[
L=1,\qquad \Gamma=1,
\]

with regularized core ratio

\[
\epsilon_c=a/L.
\]

The solver integrates the regularized Biot–Savart centerline equation with RK4 and

\[
\Delta \hat t
=4\pi C_{\rm CFL}\frac{(\Delta\hat s_{\min})^2}{|\Gamma|}.
\]

Since \(\Gamma=1\) in the blind stage, no dimensional circulation scale enters.

## 2. Adaptive arclength gauge control

Tangential marker redistribution is treated as a centerline parametrization operation, not physical forcing. v0.3.1 triggers uniform-arclength reparameterization when either

\[
CV(\Delta s)>CV_{\rm trigger}
\]

or the edge ratio exceeds its preregistered trigger. The campaign logs the largest mesh defect observed **before** cleanup. The scientific gate therefore cannot be made to pass merely because a bad mesh was redistributed after the fact.

A dynamic step budget is computed from the initial CFL estimate and the requested horizon, multiplied by a preregistered safety factor and bounded by an absolute cap. Exhausting that cap produces an explicit error row and fails the coverage gate.

## 3. Gauge-projected relative equilibrium

Let

\[
\mathbf u_{\rm rigid}(\mathbf X)
=\mathbf U+\boldsymbol\Omega\times\mathbf X.
\]

The full marker residual is

\[
\epsilon_{\rm RE}^{\rm full}
=\frac{\|\mathbf u-\mathbf u_{\rm rigid}\|}{\|\mathbf u\|}.
\]

For an unlabelled centerline, define the local tangent \(\mathbf t\) and normal projector

\[
P_\perp=I-\mathbf t\mathbf t^T.
\]

The centerline residual is

\[
\boxed{
\epsilon_{\rm RE}^{\perp}
=\frac{\|P_\perp(\mathbf u-\mathbf u_{\rm rigid})\|}
       {\|P_\perp\mathbf u\|}
}.
\]

v0.3.1 gates on \(\epsilon_{\rm RE}^{\perp}\). The full residual is retained as a material-marker diagnostic only.

## 4. Dedicated mode discovery

The Universal-Action amplitudes are not used to choose the spatial mode. A separate small broadband normal probe is evolved first. From its odd response,

\[
\delta\mathbf X_{\rm odd}(t)
=\frac{\mathbf X_+(t)-\mathbf X_-(t)}{2A_{\rm probe}},
\]

a POD/SVD discovery produces a leading response vector \(\phi_{\rm raw}\).

This vector is projected into the local normal bundle:

\[
\phi_\perp=P_\perp\phi_{\rm raw},
\]

then RMS-normalized and frozen. The blind gate requires a minimum normal-content fraction so a predominantly tangential/gauge mode cannot be promoted as a shape mode.

## 5. Matched mode energy and frequency

For each action amplitude \(A\), the exact same frozen mode is used for both energy and dynamics:

\[
\mathbf X_{\pm}(A)=\mathcal N_L\left[\mathbf X_0\pm A\phi_\perp\right],
\]

where \(\mathcal N_L\) recenters and restores the normalized total arclength.

The dimensionless energy diagnostic is

\[
\hat E
=\frac{1}{8\pi}
\sum_{ij}
\frac{\Delta\boldsymbol\ell_i\cdot\Delta\boldsymbol\ell_j}
{\sqrt{|\mathbf m_i-\mathbf m_j|^2+\epsilon_c^2}}.
\]

The matched symmetric mode-energy response is

\[
\boxed{
\Delta\hat E_\phi(A)
=\frac{\hat E[\mathbf X_+(A)]+\hat E[\mathbf X_-(A)]}{2}
-\hat E[\mathbf X_0]
}.
\]

The same \(\mathbf X_\pm(A)\) pair is evolved, and the odd trajectory is projected onto the frozen \(\phi_\perp\) to measure

\[
\hat f_\phi(A),\qquad
\hat\omega_\phi(A)=2\pi\hat f_\phi(A).
\]

Therefore

\[
\hat J_{f,\phi}=\frac{\Delta\hat E_\phi}{\hat f_\phi},
\qquad
\hat J_{\omega,\phi}=\frac{\Delta\hat E_\phi}{\hat\omega_\phi}
\]

are mode-matched by construction.

## 6. Iterative frequency-horizon certification

A dominant peak in the first non-zero FFT bin is classified as window limited. It is not interpreted as an intrinsic frequency.

Starting from \(T_0\), v0.3.1 repeats the same frozen-mode experiment with increasing dimensionless horizon:

\[
T_0<T_1<T_2<\cdots<T_{\max}.
\]

The horizon is increased until all target-free window criteria are met or a preregistered cap is reached. A resolved certification requires, at minimum,

\[
k_{\rm FFT}>1
\]

and

\[
N_{\rm cycles}\ge N_{\rm target}.
\]

Spectral concentration and harmonic quality remain separate recurrence gates. If the horizon cap is reached, the result remains unresolved.

The certified horizon from the smallest action amplitude is then frozen for all other action amplitudes at that carrier/resolution, preventing amplitude-dependent observation windows from biasing the action slope.

## 7. Temporal convergence

Temporal refinements use

- the same base geometry;
- the same frozen mode;
- the same perturbation amplitude;
- the same physical dimensionless final time;
- different CFL divisors only.

Only resolved frequencies are eligible for the temporal convergence comparison.

## 8. Complete numerical coverage

The preregistered expected observation count is

\[
N_{\rm expected}=N_C N_N N_A.
\]

Every slot must produce an explicit row. Numerical failures produce `row_status=ERROR` rather than silently deleting data. The public campaign JSON records expected, observed, OK, and error counts.

## 9. Blind Universal-Action gates

### UA0 — no SST/SI/target leak
No canonical SST constant, SI action scale, or absolute target appears in the pre-reveal path.

### UA0b — complete campaign coverage
All preregistered rows exist and have `row_status=OK`.

### UA1 — frequency convention
\[
\hat\omega=2\pi\hat f.
\]

### UA2 — recurrent frozen mode
A resolved, non-window-limited mode must meet the configured cycle, spectral-power, and harmonic-fit thresholds.

### UA2a — frozen mode normal content
The discovered frozen mode must contain sufficient centerline-normal content.

### UA2b — normal relative equilibrium
\[
\epsilon_{\rm RE}^{\perp}\le\epsilon_{\rm RE,max}.
\]

### UA2c — positive resolved mode energy
\[
\Delta\hat E_\phi>0
\]
with the configured minimum relative signal.

### UA2d — matched mode identity
Energy and frequency must explicitly be derived from the same frozen mode.

### UA3 — adaptive mesh quality
Maximum pre-cleanup mesh CV and edge ratio must remain below the hard scientific limits.

### UA3b — temporal convergence
The frozen-mode frequency must converge under the configured CFL refinement ladder.

### UA4 — reject classical continuous action
For

\[
\hat J_f(A)\propto A^{p_A},
\]

a well-resolved positive \(p_A\) near the classical quadratic-energy expectation is a null trigger, not evidence of quantization.

### UA5 — amplitude independence
A universal-action candidate requires

\[
|p_A|\le p_{\max}.
\]

### UA6 — cross-carrier universality
The coefficient of variation of accepted \(\hat J_f\) values must pass the preregistered threshold.

### UA7 — spatial convergence
Highest-resolution medians must converge within the configured tolerance.

## 10. Prerequisite semantics

If recurrence, frozen-mode validity, mesh quality, relative equilibrium, positive mode energy, or temporal convergence is missing, downstream action gates are reported as

```text
SKIP_PREREQUISITE
```

rather than being overinterpreted as an independent physical failure or success.

## 11. Reveal dimensionalization

Only after the blind result is frozen may independently sourced dimensional scales be supplied:

\[
E_{\rm phys}=\rho\Gamma^2L\,\hat E,
\qquad
f_{\rm phys}=\frac{\Gamma}{L^2}\hat f.
\]

Hence

\[
\frac{\Delta E_{\rm phys}}{f_{\rm phys}}
=\rho\Gamma L^3\frac{\Delta\hat E}{\hat f}.
\]

Define

\[
J_0=\rho\Gamma L^3.
\]

An absolute comparison with \(h\) or \(\hbar\) is eligible only when the provenance of \(J_0\) is independently justified.

## 12. Floquet restriction

The POD/frequency machinery in this falsifier is not called a Floquet spectrum. A true Floquet monodromy claim requires an accepted relative-periodic orbit and a variational evolution around that orbit.
