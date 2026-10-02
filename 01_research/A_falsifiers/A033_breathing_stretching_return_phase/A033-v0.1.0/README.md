# SST Breathing–Stretching–Return-Phase Causality Blind Falsifier v0.1.1

Purpose: test one narrow claim:

> A closed finite-core-like vortex filament can support a coherent breathing/stretching ripple whose **measured** loop return phase predicts the subsequent restoring response of the global collapse/expand coordinate.

This release is deliberately **not** a proof of the SST Swirl Clock. It tests a hydrodynamic prerequisite.

## Hard prohibitions

The simulation/scoring path contains no user-set `tau_delay`, `feedback_delay`, return time, or target phase. The return time is detected from the evolving differential stretch field. The physical meanings of the two treatment-arm signs are hidden until `run_reveal.cmd`.

## Model

The centerline evolves with a regularized Biot–Savart filament kernel. In the primary branch the desingularization radius is a **material core variable**, not a fixed plotting parameter:

\[
\dot{\mathbf X}(s_i)=\frac{\Gamma}{4\pi}\sum_j
\frac{\Delta\mathbf X_j\times(\mathbf X_i-\mathbf X_{j+1/2})}
{\left(|\mathbf X_i-\mathbf X_{j+1/2}|^2+a^2\right)^{3/2}}.
\]

For each Lagrangian segment, incompressible material-tube volume conservation is imposed as

\[
a_j^2(t)\,\ell_j(t)=a_{j0}^2\,\ell_{j0},
\qquad
 a_j(t)=a_{j0}\sqrt{\frac{\ell_{j0}}{\ell_j(t)}}.
\]

That segment-dependent \(a_j(t)\) is fed back into the next Biot–Savart/RK4 evaluation. Thus vortex stretching is part of the **dynamics**, rather than merely a recorded diagnostic. The measured line-stretch rate is

\[
\sigma_j=\frac{1}{\ell_j}(\mathbf u_{j+1}-\mathbf u_j)\cdot\hat{\mathbf t}_j
\approx \hat{\mathbf t}^{\!T}(\nabla\mathbf u)\hat{\mathbf t},
\]

and, for an ideal incompressible material vortex tube,

\[
\frac{D\ln|\boldsymbol\omega|}{Dt}=\sigma,
\qquad
\frac{D\ln a}{Dt}=-\frac{\sigma}{2}.
\]

A matched **fixed-core null** repeats the extended campaign with exponent zero, \(a_j(t)=a_{j0}\). A stretch-mediated claim is not promoted if this null produces the same phase-causality result.

The global breathing coordinate is based on the arclength-weighted radius of gyration

\[
q(t)=\frac{R_g(t)}{R_g(0)}-1.
\]

A matched pair has identical carrier, breathing arm and packet location, but opposite **anonymous** ripple arm. Pair differencing isolates the ripple-sensitive stretching field

\[
\Delta\sigma=\frac{\sigma_{+}-\sigma_{-}}{2}.
\]

Circular cross-correlation tracks this packet around the material coordinate. `tau_return` is the first measured full-loop crossing; it is never supplied to the dynamics.

The breathing clock is required to be a coherent harmonic rather than an arbitrary Hilbert phase. Around the dominant spectral peak the code refines \(\omega_b\) and fits

\[
q(t)\simeq q_0+A_c\cos(\omega_b t)+A_s\sin(\omega_b t),
\]

so the measured return phase is

\[
\phi_{\rm ret}=\omega_b t_{\rm ret}-\operatorname{atan2}(A_s,A_c)\pmod{2\pi}.
\]

Coefficient covariance, frequency-grid resolution, and packet-return-time uncertainty are propagated into `return_phase_uncertainty_rad`; a primary-valid pair requires this to be at most \(0.25\,\mathrm{rad}\).

The anonymous differential post-return acceleration is converted to a restoring response

\[
Y=-q(t_{\rm ret})\,\Delta\ddot q_{\rm post}.
\]

The primary across-carrier test is a carrier-held-out circular regression

\[
Y=\beta_0+\beta_c\cos\phi_{\rm ret}+\beta_s\sin\phi_{\rm ret}+\epsilon.
\]

## Primary gate

A positive phase-causality candidate requires all of the following in the blind score:

1. at least 6 valid pairs from at least 3 anonymous carriers;
2. packet amplitude/correlation, propagation monotonicity, coherent breathing-harmonic, return-phase uncertainty, and Lagrangian mesh-quality gates pass;
3. leave-one-carrier-out \(R^2\ge 0.10\);
4. carrier-grouped phase permutation \(p\le 0.01\);
5. median pre-return anonymous differential acceleration is no more than 75% of the post-return magnitude;
6. the measured full-return circular model must beat the preregistered half-return / three-quarter-return temporal-null models by at least \(\Delta R^2_{\rm CV}=0.03\).

The last two items guard against interpreting purely instantaneous nonlocal Biot–Savart coupling, or a generic breathing-phase correlation, as delayed feedback.

## Run

From the unzipped directory:

```bat
run_all.cmd
```

Default dataset:

```text
..\..\KnotPlot\knots\final
```

Or explicitly:

```bat
run_all.cmd C:\workspace\projects\SST-Workbench\KnotPlot\knots\final
```

The BASIC chain deliberately stops before semantic reveal. Inspect:

```text
outputs\basic\results\blind_summary.json
outputs\basic\results\blind_pair_results.csv
```

Then reveal only after the blind verdict is frozen:

```bat
run_reveal.cmd outputs\basic
```

Extended + fixed-core stretching null:

```bat
run_all_extended.cmd C:\workspace\projects\SST-Workbench\KnotPlot\knots\final
run_reveal.cmd outputs\extended
```

The extended chain also writes:

```text
outputs\stretch_mediation_summary.json
```

`stretch_mediation_gate = PASS` requires the material-core branch to pass the primary phase gate, the fixed-core null not to pass it, and \(\Delta R^2_{\rm CV}\ge0.05\) in favor of the material-core branch.

Resolution ladder (same blinded conditions at \(N=64,96,128\)):

```bat
run_resolution.cmd C:\workspace\projects\SST-Workbench\KnotPlot\knots\final
```

This writes `outputs\resolution_summary.json` and requires the high-resolution step \(96\rightarrow128\) to satisfy median gates of 10% for return time, 0.25 rad for return phase, and 25% for restoring response.

## Interpretation discipline

`PASS` means only: within this regularized filament model, a measured full-loop stretching-ripple return phase contains held-out predictive information about the subsequent restoring response, beyond the preregistered pre-return contamination guard.

It does **not** establish full 3-D Euler finite-core stability, a unique physical time standard, relativistic time dilation, or the SST ontology. The decisive next level after a pass is a volumetric vorticity solver with pressure-Poisson closure and the same frozen gates.

## Canonical SST scale (reported, not fitted)

Using

\[
\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}=1.09384563\times10^6\ \mathrm{m\,s^{-1}},\qquad
r_c=1.40897017\times10^{-15}\ \mathrm{m},
\]

the corresponding circulation scale is

\[
\Gamma_c=2\pi r_c\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}
=9.68361920349\times10^{-9}\ \mathrm{m^2\,s^{-1}}.
\]

The campaign itself is nondimensional because the imported KnotPlot geometries have arbitrary overall scale; this avoids smuggling an unmeasured physical size into the causality test.

## References

```latex
\begin{thebibliography}{99}
\bibitem{Helmholtz1858}
H. Helmholtz (1858),
``Über Integrale der hydrodynamischen Gleichungen, welche den Wirbelbewegungen entsprechen,''
\emph{Journal für die reine und angewandte Mathematik} \textbf{55}, 25--55.
https://eudml.org/doc/147745

\bibitem{Saffman1992}
P. G. Saffman (1992),
\emph{Vortex Dynamics}, Cambridge University Press.
https://doi.org/10.1017/CBO9780511624063

\bibitem{Leonard1985}
A. Leonard (1985),
``Computing three-dimensional incompressible flows with vortex elements,''
\emph{Annual Review of Fluid Mechanics} \textbf{17}, 523--559.
https://doi.org/10.1146/annurev.fl.17.010185.002515
\end{thebibliography}
```
