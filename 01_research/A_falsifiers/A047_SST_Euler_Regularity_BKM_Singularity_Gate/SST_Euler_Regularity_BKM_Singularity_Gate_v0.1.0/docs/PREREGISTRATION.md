# A043 v0.1.0 preregistration

## Primary falsification question

For dimensionless, smooth trefoil-tube initial data evolved by the 3-D incompressible unforced Euler equations, does the tested trajectory produce a **numerically valid, cross-run convergent finite-time singularity candidate** under the preregistered BKM-screening heuristic?

## Primary observable

\[
B(t)=\int_0^t \|\boldsymbol\omega(s)\|_{L^\infty}\,ds,
\qquad
M_\omega(t)=\|\boldsymbol\omega(t)\|_{L^\infty}.
\]

The screening fit uses the late-window affine proxy

\[
M_\omega(t)^{-1}\approx a t+b,
\qquad
T_*=-b/a,
\]

only when \(a<0\). This is a **heuristic detector**, not a sufficient mathematical criterion for blow-up.

## Frozen v0.1.0 numerical validity gates

\[
\frac{|E(T)-E(0)|}{|E(0)|}<5\times10^{-3},
\qquad
\max_t \|\nabla\cdot\mathbf u\|_{\rm RMS}<10^{-10}.
\]

A single-run candidate additionally requires \(R^2\ge0.98\) and \(T<T_*\le1.5T\). Global escalation requires at least three numerically valid candidates and relative spread of their estimated \(T_*\) below 10%.

## Blindness

The BLIND output contains only hashed case IDs, grid/time metadata and diagnostics. Human-readable condition labels, packet amplitudes and all SST canonical constants are revealed only after the blind assessment is frozen.

## Scope limits

The periodic pseudo-spectral calculation is not a reproduction of the compactly supported \(\mathbb R^3\) construction of OpenAI (2026). The localized packet is an adversarial proxy inspired by the paper's deformation/wave-amplification mechanism, not an implementation of its exact iterative proof construction.
