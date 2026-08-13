# Theory and gates — v0.1.0

## A. Dimensionless SST normalization

The workbench uses

\[
\hat{\mathbf x}=\mathbf x/r_c,
\qquad
\hat t=t\,\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}/r_c,
\qquad
\hat\Gamma=\Gamma/(r_c\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}).
\]

With the canonical circulation ansatz used only as a scale diagnostic,

\[
\Gamma_{\rm SST}=2\pi r_c\mathbf{v}_{\!\boldsymbol{\circlearrowleft}},
\qquad \hat\Gamma=2\pi.
\]

## B. K0 paper equation

For the long-wave \(m=1\) Kelvin branch,

\[
\omega(k)=-\frac{\Gamma}{4\pi}k^2
\left[\ln\left(\frac{2}{|k|a_0}\right)-\gamma_E+\frac14\right].
\]

K0 solves the full Rankine dispersion residual numerically and checks the small-\(ka_0\) and large-\(ka_0\) limits. The large-wave-number check is deliberately made at \(ka_0=6\), not merely around unity where the asymptotic is not yet accurate.

## C. Model hierarchy

`PAPER_EQUATION_NUMERICAL_REPRODUCTION` means the experimental paper's analytical equation was reproduced numerically.

`REGULARIZED_BIOT_SAVART_*` means a centerline closure was used. It does not establish a unique finite-core SST profile.

`FROZEN_LOCAL_KELVIN_SPECTRUM` is a Jacobian/eigenmode diagnostic around a specified geometry. It is not a Floquet spectrum unless a periodic or relative-periodic base trajectory has independently been demonstrated.

`TRUE_RELATIVE_FLOQUET` is reserved for

\[
M=D(g_*^{-1}\circ\phi_T)_{X_0}
\]

on an accepted relative periodic orbit.

## D. RPO/Floquet rule

The intended logical implication is

\[
\mathrm{RPO\ accepted}
\Longrightarrow
\mathrm{relative\ monodromy\ eligible}.
\]

The converse is forbidden operationally: if the RPO is not accepted, K6 becomes `SKIP` and no monodromy output is manufactured.

## E. Resonance search

K7 starts from the numerical mode map \(m\mapsto\omega_m\). It searches both 4-wave and 6-wave frequency detunings subject to mode-index conservation, discarding permutations that contain the same incoming and outgoing multisets.

The six-wave combination phase is

\[
\Theta_6=\phi_1+\phi_2+\phi_3-\phi_4-\phi_5-\phi_6.
\]

The normalized sixth-order coherence is

\[
P_6=
\frac{\left|\langle a_1^*a_2^*a_3^*a_4a_5a_6\rangle\right|}
{\sqrt{\langle|a_1a_2a_3|^2\rangle
\langle|a_4a_5a_6|^2\rangle}}.
\]

A high value is a phase-correlation diagnostic. By itself it is not proof of a universal SST Hamiltonian coefficient.

## F. Broadband diagnostic

The current Phase IV run is initialized, not continuously forced. Accordingly the workbench calls

\[
\Pi(m_c)\sim-\frac{d}{dt}\sum_{m\le m_c}E_m
\]

a **transfer-flux proxy**, not a stationary weak-turbulence cascade flux. A future forced/dissipative or conservative recurrence-controlled campaign should implement the stronger energy-budget closure.

## G. Chirality test

K13 evaluates

\[
(K,+\Gamma),\quad(K,-\Gamma),\quad(\bar K,+\Gamma),\quad(\bar K,-\Gamma)
\]

with otherwise identical numerical parameters. Partner differences are reported rather than interpreted post hoc.

## H. Target-blind rule

No measured fine-structure target is imported by the scientific modules. K14 scans the Python package and C++ kernel for predeclared numerical target strings. A target comparison, if ever desired, must be a later, isolated analysis after the blind archive is frozen.

## References

```latex
\begin{thebibliography}{99}
\bibitem{Barckicke2026KWT}
J.~Barckicke, C.~Gissinger, and E.~Falcon,
``Experimental evidence of Kelvin-wave turbulence along a vortex core,''
\textit{Physical Review Letters} (2026), doi:10.1103/t3bt-m431,
\url{https://arxiv.org/abs/2607.07535}.

\bibitem{Floquet1883}
G.~Floquet,
``Sur les equations differentielles lineaires a coefficients periodiques,''
\textit{Annales scientifiques de l'Ecole Normale Superieure}, Serie 2,
\textbf{12}, 47--88 (1883), doi:10.24033/asens.220.
\end{thebibliography}
```
