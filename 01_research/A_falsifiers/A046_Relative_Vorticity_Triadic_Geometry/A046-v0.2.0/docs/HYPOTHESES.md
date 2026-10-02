# A046 v0.2.0 preregistered hypotheses

## H1 — HWC is not locally complete

The retained control constructs equal local \(\mathbf u\), \(\boldsymbol\omega\), helicity, and
closed-loop circulation with unequal strain. HWC is rejected as a locally complete basis if the
HWC equality error is below \(10^{-12}\) while the strain distance exceeds \(10^{-6}\).

## H2 — UWS is complete for local first-order kinematics

\[
\partial_j u_i=S_{ij}+W_{ij},
\qquad
W_{ij}=-\frac12\epsilon_{ijk}\omega_k.
\]

The reconstructed gradient must agree with the directly differentiated gradient to relative
\(L_2<10^{-12}\). This is a kinematic completeness statement, not a gravity theorem.

## H3 — passive clock/pressure elimination

For blind dimensionless \(q=\|u\|^2/c_*^2\),

\[
\delta p_*=-\frac12q,
\qquad
n-1=(1-q)^{-1/2}-1
=(1+2\delta p_*)^{-1/2}-1.
\]

Exact relative residual must be below \(10^{-12}\).

## H4 — organized-stress Poisson response

\[
Q=\partial_i\partial_j(u_i u_j),
\qquad
\nabla^2\Phi=Q.
\]

Poisson reconstruction must have relative \(L_2<10^{-10}\), and more than 1% of the solved
\(\Phi^2\) must lie outside the strongest 10% of local \(|Q|\).

## H5 — exploratory metric controls

The v0.1 weak metric ansatz is retained. It must preserve Lorentzian signature, have zero curvature
for the constant-flow null, nonzero curvature for ABC flow, and obey lowered-Riemann pair symmetry
within the preregistered tolerance.

A new constant planetary absolute-vorticity background must also remain curvature-free in the local
tangent-frame control. This prevents uniform background rotation alone from being mislabeled as
local curvature by the ansatz.

## H6 — objectivity

The local invariants and the rotating-frame absolute-vorticity construction must be covariant under
proper rigid rotations \(Q\in SO(3)\).

## H7 — rotating-frame closure

\[
\boldsymbol\omega_{\rm abs}=\boldsymbol\omega_{\rm rel}+2\boldsymbol\Omega_p.
\]

The implementation must reproduce this identity, recover \(\boldsymbol\omega_{\rm rel}\) when
\(\Omega_p\to0\), and preserve a matched north/south cyclonic mirror relation in local tangent
frames.

## H8 — delay / circulation memory

A blind periodic circulation signal must recover the imposed

\[
\Delta\phi=\omega\tau
\]

within \(10^{-10}\) rad. The memory response

\[
M_\tau=\Gamma(t)-\Gamma(t-\tau)
\]

must vanish for \(\tau=0\) and be nonzero for the preregistered finite delay.
