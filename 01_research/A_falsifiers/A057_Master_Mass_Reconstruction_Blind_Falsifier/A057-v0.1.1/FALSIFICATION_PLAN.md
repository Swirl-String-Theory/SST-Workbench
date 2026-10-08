# Falsification plan — A057 v0.1.1

## Primary causal chain under test

\[
\text{PKLSA geometry}
\rightarrow \widehat H_K
\rightarrow L(q,\dot q)\leftrightarrow H(q,p)
\rightarrow \nabla_q^2H
\rightarrow J_K
\rightarrow \operatorname{spec}J_K
\rightarrow \Lambda_K
\rightarrow \text{frozen protected predictions}.
\]

The historical factorized equations are competitors, not privileged targets. The blind campaign first asks whether a geometry/dynamics kernel exists at all.

## Physical energy target and operational kernels

The physical reference object is the three-dimensional rest-mass functional

\[
M_K^{(3D)}=\frac{1}{2c^2}\int \rho_K(\mathbf x)\|\mathbf v_K(\mathbf x)\|^2\,d^3x.
\]

A057 evaluates two reduced routes against this target: the regularized line Hamiltonian below and a Bishop-frame tube-support velocity quadrature. Agreement between the two is diagnostic evidence; disagreement is retained rather than tuned away.

## Operational finite-core Hamiltonian

For closed filament components \(K_i\), A057 evaluates

\[
H_a=\frac{\rho\Gamma^2}{8\pi}\sum_{i,j}
\oint_{K_i}\!\oint_{K_j}
\frac{d\mathbf X_i\cdot d\mathbf X_j}
{\sqrt{\|\mathbf X_i-\mathbf X_j\|^2+a^2}}.
\]

The carrier geometry is independently resampled and normalized by an estimated reach so that the dimensionless core scale is explicit. A core-scale sweep and resolution ladder are never pooled with different carriers.

## Reduced variational sector

Small perturbations are constructed in a periodic Bishop frame. With registered modal coordinates \(q\),

\[
L=\tfrac12\dot q^TM\dot q-U(q),\qquad
H=\tfrac12p^TM^{-1}p+U(q),
\]

\[
K_H=\nabla_q^2U(0),\qquad
J=\begin{pmatrix}0&I\\-M^{-1}K_H&-M^{-1}G\end{pmatrix}.
\]

The v0.1.1 baseline uses \(G=0\). A nonzero gyroscopic term is not inferred from a desired spectrum.

## Diagnostic-continuation rule

Framework prerequisites deliberately do not encode the scientific interpretation DAG. The scientific DAG is *soft*:

- source qualification strengthens all later claims;
- geometry convergence strengthens energy claims;
- stationarity strengthens Hessian/Jacobian stability interpretation;
- backend parity strengthens certification;
- independent-source replication strengthens topology-class promotion.

Failure of any of these does not suppress later numerical experiments. Instead the downstream record is retained with a machine-readable caveat. This preserves information while preventing a downstream diagnostic from being promoted beyond its support.

## Blindness

The BLIND tree contains no protected observed mass targets, protected human identity map, or protected historical numerical comparison constants. Full topology tables are frozen first. Reveal can therefore select/compare targets only after the predictions already exist byte-for-byte.

## Evidence classes

Synthetic controls test implementation only. Cross-source scientific replication requires independent-source evidence and distinct E010 provenance/independence groups.
