# Theory and preregistered gates -- v0.4.0

## 1. State and clock

Let

\[
\mathbf X=(\mathbf X_+,\mathbf X_-),
\qquad
\Gamma_-=-\Gamma_+.
\]

The regularized Biot--Savart solver defines the temporal vector field \(F(\mathbf X)\). The nondimensional time is

\[
\hat t=\Omega_\Gamma t,
\qquad
\Omega_\Gamma=\frac{\Gamma_{\rm scale}}{4\pi D^2}.
\]

For geometric centerline evolution, the tangential gauge is removed:

\[
F_\perp=F-(F\cdot t)t.
\]

No alpha-derived time or phase scale enters this evolution.

## 2. Relative periodic orbit

An RPO is a trajectory satisfying

\[
\phi_T(\mathbf X_0)=g\mathbf X_0,
\]

for an allowed continuous symmetry \(g\in SE(3)\), modulo common cyclic relabelling of the polygon vertices. Numerically,

\[
\varepsilon_{\rm RPO}
=\frac{\|g_*\phi_T(\mathbf X_0)-\mathbf X_0\|_{\rm RMS}}{D}.
\]

The same \(g_*\) must map the endpoint vector field back to the initial field:

\[
\varepsilon_f
=\frac{\|g_*F(\mathbf X(T))-F(\mathbf X_0)\|}{\|F(\mathbf X_0)\|}.
\]

This prevents a geometrically accidental near-return from being mistaken for an invariant orbit.

## 3. Relative monodromy

For an accepted RPO, the relevant return operator is

\[
\mathcal P=g_*^{-1}\circ\phi_T.
\]

The true relative monodromy is

\[
\boxed{\mathbf M=D\mathcal P(\mathbf X_0)}.
\]

v0.4 differentiates the complete nonlinear time-\(T\) map by central finite differences. This includes the full time dependence of the variational operator along the orbit. It is therefore logically different from the frozen approximation

\[
\exp[J(\mathbf X_0)T].
\]

The latter remains a v0.3 diagnostic only.

## 4. Multiplier checks

If \(\mu_j\) are eigenvalues of \(\mathbf M\), a genuine periodic flow direction should give a neutral multiplier near unity. v0.4 tests this directly through

\[
\varepsilon_{\rm neutral}
=\frac{\|\mathbf M F_0-F_0\|}{\|F_0\|}.
\]

Since \(\mathbf M\) is real, its non-real eigenvalues must occur in complex-conjugate pairs. Reciprocal pairing is reported only diagnostically because the implemented Cartesian filament discretization has not been proven to be a canonical symplectic discretization.

## 5. Gate logic

- **H0** blind source check.
- **H1** C++/Python RHS parity.
- **H2** RK4 convergence in the observed asymptotic step-size regime.
- **H3** exact recovery after a known `SE(3)` transform.
- **H4** scale collapse.
- **H5** recurrence minimization is well posed.
- **H6/H7** canonical seed controls.
- **H8** existence of at least one accepted preregistered blind RPO.
- **H9** full relative monodromy constructed.
- **H10** time-tangent neutral check.
- **H11** monodromy finite-difference convergence.
- **H12** conjugate-pair spectral closure.
- **H13** preregistered true-Floquet phase readout is finite and sufficiently contained in the Kelvin subspace.
- **H14** permission to unblind alpha.

If H8 fails, H9--H13 are **SKIP**, not numerical failures. A Floquet calculation without a periodic base orbit is scientifically undefined for the intended claim.

## 6. Search-domain limitation

The v0.4.0 reference campaign is a bounded falsification attempt, not a proof of nonexistence. A negative result only excludes the preregistered seed domain and time window at the tested finite-core closure/resolutions.

## References

```latex
\bibitem{Floquet1883}
G.~Floquet,
``Sur les équations différentielles linéaires à coefficients périodiques,''
\textit{Annales scientifiques de l'École Normale Supérieure}, 2e série, \textbf{12}, 47--88 (1883).
doi:10.24033/asens.220.

\bibitem{Hasimoto1972}
H.~Hasimoto,
``A soliton on a vortex filament,''
\textit{Journal of Fluid Mechanics} \textbf{51}, 477--485 (1972).
doi:10.1017/S0022112072002307.

\bibitem{Viswanath2007}
D.~Viswanath,
``Recurrent motions within plane Couette turbulence,''
\textit{Journal of Fluid Mechanics} \textbf{580}, 339--358 (2007).
doi:10.1017/S0022112007005459.
```
