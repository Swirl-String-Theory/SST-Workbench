# Preregistered hypotheses and rejection criteria

## H1 — HWC is not locally complete

Candidate:
\[
\mathcal B_{\rm HWC}=\{h,\boldsymbol{\omega},\Gamma\},
\qquad h=\mathbf u\cdot\boldsymbol{\omega}.
\]

Control pair:
\[
\mathbf u_A=(-\Omega y,\Omega x,0),
\]
\[
\mathbf u_B=(-\Omega y+a x,\Omega x-a y,0).
\]

Both are incompressible. At the origin they have equal velocity, vorticity,
helicity density, and loop circulation, while
\[
S^{(A)}_{ij}=0,\qquad
S^{(B)}_{ij}=\operatorname{diag}(a,-a,0).
\]

**Rejection rule:** if the HWC observables are equal within \(10^{-12}\)
while \(\|S_A-S_B\|_F>10^{-6}\), classify HWC as
`REJECTED_AS_LOCAL_COMPLETE_BASIS`.

## H2 — UWS distinguishes the pair

Candidate:
\[
\mathcal B_{\rm UWS}=\{\mathbf u,\boldsymbol{\omega},S_{ij}\}.
\]

The local first-order decomposition is
\[
\partial_j u_i=S_{ij}+W_{ij},
\]
\[
S_{ij}=\frac12(\partial_j u_i+\partial_i u_j),
\qquad
W_{ij}=-\frac12\epsilon_{ijk}\omega_k.
\]

Survival of this gate establishes only local discriminability.

## H3 — pressure/clock elimination

For a blind dimensionless speed scale \(c_\star\),
\[
q=\frac{\|\mathbf u\|^2}{c_\star^2},\quad
\delta p_\star=-\frac12q,\quad
n=(1-q)^{-1/2}.
\]

Exact elimination:
\[
n-1=(1+2\delta p_\star)^{-1/2}-1.
\]

Gate: relative \(L_2<10^{-12}\).

The leading relation
\[
n-1=-\delta p_\star+O(q^2)
\]
is reported but not used as an exact gate.

## H4 — organized-stress Poisson response

\[
Q=\partial_i\partial_j(u_i u_j),\qquad \nabla^2\Phi=Q.
\]

Gates:
- Poisson reconstruction relative \(L_2<10^{-10}\).
- More than 1% of \(\Phi^2\) lies outside the strongest 10% of \(|Q|\).

## H5 — exploratory metric

Static preregistered ansatz:
\[
g_{00}=-(1-\beta^2),
\qquad
g_{0i}=\epsilon_\omega\frac{\omega_i}{\omega_{\rm rms}},
\]
\[
\gamma_{ij}=\delta_{ij}
+\epsilon_S\frac{S_{ij}}{S_{\rm rms}}
+\epsilon_{\omega2}
\left[
\frac{\omega_i\omega_j}{\omega_{\rm rms}^2}
-\frac{\|\boldsymbol{\omega}\|^2}{3\omega_{\rm rms}^2}\delta_{ij}
\right].
\]

This is an **exploratory ansatz**, not a Canon equation.

Gates:
- exactly one negative metric eigenvalue everywhere;
- constant-flow control: curvature RMS \(<10^{-12}\);
- nonuniform ABC control: curvature RMS \(>10^{-6}\);
- lowered-Riemann pair-symmetry relative residual \(<10^{-3}\).

## H6 — objectivity

Under a rigid \(Q\in SO(3)\):
\[
\mathbf u\mapsto Q\mathbf u,\quad
\boldsymbol{\omega}\mapsto Q\boldsymbol{\omega},\quad
S\mapsto QSQ^T.
\]

The scalar invariants
\(\|\mathbf u\|^2,\|\boldsymbol{\omega}\|^2,\|S\|_F^2,h\)
must be preserved.
