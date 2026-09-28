# C006 v0.3.0 — Theory and gates

## A. Time convention

The local projected temporal operator is

\[
\frac{d q}{d\hat t}=Gq,
\qquad Gv_j=\lambda_jv_j,
\qquad \lambda_j=\sigma_j+i\omega_j.
\]

Therefore

\[
q_j(\hat t)\propto e^{\lambda_j\hat t}
=e^{\sigma_j\hat t}e^{i\omega_j\hat t}.
\]

`Re(lambda)` is growth/decay and `Im(lambda)` is oscillation. This convention must not be confused with a QNM ansatz in which damping may appear in the imaginary part of a complex frequency.

The C006 circulation clock is

\[
\hat t=\Omega_\Gamma t,
\qquad
\Omega_\Gamma=\frac{\Gamma_{\rm scale}}{4\pi D^2}.
\]

## B. K15 stable-root tracking

For neighboring resolution levels, roots are matched by minimizing total normalized complex-plane distance

\[
d_{ij}=\frac{|\lambda_i^{(N_a)}-\lambda_j^{(N_b)}|}
{\max(|\lambda_i^{(N_a)}|,|\lambda_j^{(N_b)}|,\epsilon)}.
\]

The assignment is global and one-to-one. A branch passes persistence only if every step satisfies the pre-registered threshold.

This is the C006 adaptation of the robust-root principle used by Batic & Dutykh when comparing QNM roots across increasing spectral resolution. The underlying physical operators are different.

## C. Generic quadratic eigenvalue infrastructure

The reusable QEP form is

\[
Q(\lambda)x
=\left(M_0+\lambda M_1+\lambda^2M_2\right)x=0.
\]

It is linearized as

\[
\begin{pmatrix}
0&I\\
-M_0&-M_1
\end{pmatrix}z
=\lambda
\begin{pmatrix}
I&0\\
0&M_2
\end{pmatrix}z.
\]

The implementation self-test uses

\[
\lambda^2+3\lambda+2=0
\]

with exact roots \(-1\) and \(-2\). C006 v0.3.0 does not convert its first-order Kelvin generator into a QEP merely to mimic the source paper.

## D. K16 continuation and non-oscillatory modes

The regularization parameter \(\varepsilon/D\) is varied while all other registered choices remain fixed. Branches are tracked by the same assignment machinery.

A temporal-generator eigenvalue is descriptively tagged `overdamped_like` when

\[
\chi_{\rm osc}=\frac{|\operatorname{Im}\lambda|}
{\max(|\lambda|,\lambda_{\rm floor})}
\leq\chi_{\max}.
\]

The tag only means that the finite-dimensional local mode has little oscillatory part under this convention. It is not a claim of viscous damping.

## E. K17 conservative spectral symmetry

For each eigenvalue \(\lambda\), K17 measures the nearest-spectrum defects for

\[
\lambda^*,\quad -\lambda,\quad -\lambda^*.
\]

For a full real Hamiltonian linearization, quartet symmetries can arise under appropriate hypotheses. C006 does not assume those hypotheses survive its four-state projected subspace. Accordingly K17 is diagnostic and cannot by itself falsify the underlying inviscid Euler dynamics.

## F. K18 finite-dimensional intertwining pretest

Using the basis ordering

```text
[h+ common, h+ differential, h- common, h- differential]
```

C006 partitions the 4×4 projected generator into common and differential 2×2 diagonal blocks plus cross-sector blocks.

The off-block coupling measure is

\[
\eta_{\rm coupling}
=
\frac{\sqrt{\|G_{cd}\|_F^2+\|G_{dc}\|_F^2}}
{\|G\|_F}.
\]

Only if this is small does a separate-sector spectral comparison become meaningful.

The numerical intertwiner pretest solves

\[
BX-XA\approx0
\]

by finding the smallest singular vector of

\[
I\otimes B-A^T\otimes I.
\]

A small residual is necessary for approximate finite-dimensional intertwining, but it is not sufficient for a Darboux claim.

## G. Darboux factorization and K19

For scalar second-order operators, a standard first-order Darboux/supersymmetric factorization has

\[
A=\frac{d}{ds}+W(s),
\qquad
A^\dagger=-\frac{d}{ds}+W(s),
\]

and partner Hamiltonians

\[
H_+=AA^\dagger,
\qquad
H_-=A^\dagger A.
\]

Batic & Dutykh use this structure to prove a specific scalar–vector isospectrality in their Einstein limit. C006 K19 requires an independently derived SST operator pair before this machinery may be promoted from a numerical self-test to physics.

K19 therefore remains `SKIP` under the present centerline model.

## H. K20 local ↔ true Floquet mapping

If the nonlinear dynamics has an accepted RPO with dimensionless period \(T\), a local constant generator would predict

\[
\mu_j^{\rm local}=e^{\lambda_j T}.
\]

K20 compares these values with eigenvalues of the actual relative monodromy

\[
M=D(g_*^{-1}\circ\phi_T)_{X_0}.
\]

The comparison is legal only after K6 accepts the RPO and constructs \(M\). Otherwise K20 is `SKIP`.

## I. Falsification semantics

- `PASS`: a pre-registered numerical implementation criterion passed.
- `WARN`: usable numerical result, but a desired convergence/cross-certification criterion did not pass.
- `DIAGNOSTIC`: descriptive result; no physical pass/fail claim.
- `SKIP`: a scientific prerequisite is absent.
- `FAIL`: hard numerical or registered criterion failed.

No threshold may be retuned after inspecting v0.3.0 output without creating a new version and recording that change.

## References

```latex
\begin{thebibliography}{99}
\bibitem{BaticDutykh2026}
D.~Batic and D.~Dutykh,
``Quasinormal Modes of Gauss--Bonnet Black Holes via the Spectral Method:
Scalar, Vector, and Tensor Perturbations,''
arXiv:2608.06083 [gr-qc] (2026),
\url{https://arxiv.org/abs/2608.06083}.

\bibitem{Trefethen2000}
L.~N.~Trefethen,
\textit{Spectral Methods in MATLAB},
SIAM, Philadelphia (2000),
doi:10.1137/1.9780898719598.

\bibitem{TisseurMeerbergen2001}
F.~Tisseur and K.~Meerbergen,
``The Quadratic Eigenvalue Problem,''
\textit{SIAM Review} \textbf{43}, 235--286 (2001),
doi:10.1137/S0036144500381988.
\end{thebibliography}
```
