# Theory and preregistered gates -- v0.5.0

## 1. Dimensionless filament dynamics

For each vortex channel,

\[
\frac{d\mathbf X}{dt}=\mathbf u_{\rm BS}[\mathbf X],
\]

with regularised Biot--Savart velocity. Define

\[
\Omega_\Gamma=\frac{|\Gamma|}{4\pi D^2},
\qquad
\hat t=\Omega_\Gamma t.
\]

Because tangential centerline velocity only relabels material markers for the geometric filament model, v0.5 evolves

\[
\frac{d\mathbf X}{d\hat t}
=\frac{\mathbf u_\perp}{\Omega_\Gamma},
\qquad
\mathbf u_\perp=\mathbf u-(\mathbf u\cdot\mathbf t)\mathbf t.
\]

## 2. Relative periodic orbit

A true RPO must satisfy

\[
\phi_T(\mathbf X_0)=g\mathbf X_0,
\qquad g\in SE(3),
\]

up to one common cyclic relabelling of both closed filaments. The recurrence metric is

\[
\epsilon_{\rm RPO}
=\frac{\operatorname{RMS}(g^{-1}\phi_T(\mathbf X_0)-\mathbf X_0)}{D}.
\]

The same fixed group action must approximately map the endpoint vector field back to the initial one.

## 3. Why `Delta s_+-` is a gauge in this model

For a closed curve \(\gamma:S^1\to\mathbb R^3\),

\[
\gamma(s)\mapsto\gamma(s+s_0)
\]

changes the parameter origin but not the embedded curve. Hence an independent constant longitudinal offset of an entire closed axisymmetric filament cannot be a new physical state coordinate. Finite polygons are not exactly invariant under fractional interpolation, so v0.5 checks that the induced discrepancy decreases with resolution.

## 4. Multiple shooting

The period is divided into \(M\) segments. Around seed nodes \(\mathbf X_j^{(0)}\), corrections are represented as

\[
\mathbf X_j=\mathbf X_j^{(0)}+D\mathbf B_j\mathbf a_j,
\]

where \(\mathbf B_j\) contains preregistered transverse Fourier/Kelvin shape modes.

For internal segments,

\[
\mathbf d_j=\phi_{T/M}(\mathbf X_j)-\mathbf X_{j+1}.
\]

For the closing segment,

\[
\mathbf d_{M-1}=g^{-1}\phi_{T/M}(\mathbf X_{M-1})-\mathbf X_0.
\]

The nonlinear residual uses projections of these defects onto the correction bases plus one phase condition.

## 5. Jacobian-free Newton--Krylov

At Newton iterate \(\mathbf z_k\),

\[
\mathbf J_F(\mathbf z_k)\delta\mathbf z=-\mathbf F(\mathbf z_k).
\]

The Jacobian is never explicitly assembled. Instead,

\[
\mathbf J_F\mathbf v
\approx
\frac{\mathbf F(\mathbf z+h\mathbf v)-\mathbf F(\mathbf z)}{h}.
\]

Restarted GMRES solves the Newton correction equation. The line search minimizes a merit function containing both projected residual and full-state shooting defect.

## 6. True Floquet monodromy

Only after a confirmed RPO does v0.5 evaluate

\[
\mathbf M
=D\!\left(g^{-1}\circ\phi_T\right)_{\mathbf X_0}
\]

by central finite differences of the complete nonlinear time-\(T\) return map. This is distinct from v0.3's frozen Jacobian exponential.

The time tangent should satisfy approximately

\[
\mathbf M\mathbf F(\mathbf X_0)\approx\mathbf F(\mathbf X_0),
\]

corresponding to a neutral Floquet multiplier near unity.

## 7. H0--H18

- **H0** alpha-blind source audit.
- **H1** native/Python RHS parity.
- **H2** RK4 convergence.
- **H3** correct `SE(3)` quotient.
- **H4** uniform-scale collapse.
- **H5** pure longitudinal channel shift converges as a relabelling gauge.
- **H6** canonical recurrence search is finite/well posed.
- **H7** preregistered alpha-blind seed campaign is finite/well posed.
- **H8** matrix-free Newton--Krylov solver returns finite residuals/GMRES diagnostics.
- **H9** full-state shooting defect decreases materially and remains bounded.
- **H10** full Cartesian RPO recurrence passes.
- **H11** endpoint vectorfield compatibility passes.
- **H12** accepted RPO survives resolution refinement.
- **H13** true relative monodromy is constructed only after H12.
- **H14** time-tangent neutral multiplier check.
- **H15** monodromy finite-difference convergence.
- **H16** complex-conjugate pairing of real monodromy spectrum.
- **H17** preregistered Kelvin true-Floquet phase is finite and sufficiently low-leakage.
- **H18** permission to import/open alpha benchmark.

## 8. Falsification logic

The following do **not** count as an RPO:

- a minimum of a coarse recurrence trace;
- a small projected Kelvin residual;
- improvement of a low-dimensional objective;
- a Floquet-like phase from a frozen local Jacobian;
- an alpha-like numerical coincidence before H18.

Only a full-state, resolution-confirmed relative recurrence with compatible dynamics may open true monodromy.

## References

```latex
\bibitem{Floquet1883}
G.~Floquet,
``Sur les équations différentielles linéaires à coefficients périodiques,''
\textit{Annales scientifiques de l'École Normale Supérieure}, Série 2, \textbf{12}, 47--88 (1883).
doi:10.24033/asens.220.

\bibitem{SaadSchultz1986}
Y.~Saad and M.~H.~Schultz,
``GMRES: A Generalized Minimal Residual Algorithm for Solving Nonsymmetric Linear Systems,''
\textit{SIAM Journal on Scientific and Statistical Computing} \textbf{7}, 856--869 (1986).
doi:10.1137/0907058.

\bibitem{KnollKeyes2004}
D.~A.~Knoll and D.~E.~Keyes,
``Jacobian-free Newton--Krylov methods: a survey of approaches and applications,''
\textit{Journal of Computational Physics} \textbf{193}, 357--397 (2004).
doi:10.1016/j.jcp.2003.08.010.

\bibitem{Viswanath2007}
D.~Viswanath,
``Recurrent motions within plane Couette turbulence,''
\textit{Journal of Fluid Mechanics} \textbf{580}, 339--358 (2007).
doi:10.1017/S0022112007005459.
```
