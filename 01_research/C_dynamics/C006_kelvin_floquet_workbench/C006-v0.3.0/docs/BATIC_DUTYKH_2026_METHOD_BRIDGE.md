# Batic–Dutykh (2026) → C006 v0.3.0 method bridge

This document separates source-derived methodology from SST adaptation.

## Source-derived items

The uploaded paper studies scalar, vector, and tensor quasinormal modes of higher-dimensional Schwarzschild black holes with Gauss–Bonnet corrections. The source reports: robust-root identification across spectral resolutions; a matrix quadratic eigenvalue problem obtained after Chebyshev collocation; overdamped/purely imaginary modes in its QNM convention; non-monotonic overtone evolution; an analytic Darboux factorization for a scalar/vector isospectral pair at vanishing Gauss–Bonnet coupling; and a six-dimensional tensor instability.

Those statements belong to the paper's gravitational model.

## C006 adaptations

C006 v0.3.0 transfers only the following methodological ideas:

- **root persistence:** recompute the Kelvin local spectrum over a frozen spatial-resolution ladder and one-to-one match roots;
- **parameter continuation:** track spectral branches over a frozen regularization scan and flag turning points;
- **QEP infrastructure:** include and self-test a generic quadratic-eigenproblem linearizer for future SST-derived second-order operators;
- **isospectrality discipline:** do not infer isospectrality from visually similar roots; first test whether sectors decouple, then seek an intertwiner, and reserve strict Darboux status for derived scalar differential operators;
- **independent dynamical confirmation:** a frozen local spectrum may be compared to true Floquet multipliers only after an independently accepted RPO.

## Explicitly not transferred

C006 v0.3.0 does not introduce:

- Gauss–Bonnet curvature;
- spacetime dimensions \(D=5,6,\ldots\);
- black-hole horizons or QNM ingoing/outgoing boundary conditions;
- DECIGO detectability claims;
- the paper's instability threshold;
- a claim that an SST Kelvin eigenvalue is a black-hole QNM;
- a claim that the present regularized filament operator is a Chebyshev-discretized finite-core Euler operator.

## Why no Chebyshev physical gate yet?

The source paper has a scalar radial boundary-value differential equation that can be compactified and collocated directly. C006 currently has a closed periodic knot centerline plus a projected temporal Biot–Savart Jacobian. A literal Chebyshev boundary-value discretization would therefore be artificial unless SST first supplies a suitable continuum perturbation operator and domain.

For the closed knot, a periodic Fourier representation is structurally more natural. The present v0.3.0 therefore implements convergence/root-tracking and QEP infrastructure without pretending that the current 4×4 generator is the same numerical object as the paper's Chebyshev QEP.

## Falsifiable next upgrade

A future C006 version may open K19 and use the QEP backend if an SST derivation supplies, for two perturbation sectors,

\[
L_j(\lambda)\psi_j=0,
\qquad j\in\{A,B\},
\]

with registered domain, boundary/periodicity conditions, finite-core closure, and normalization. At that point one can independently discretize the operators, track roots under resolution, test

\[
L_B\mathcal{A}-\mathcal{A}L_A=0,
\]

and compare the resulting local spectrum against nonlinear time-domain/Floquet behavior.

## Reference

```latex
\begin{thebibliography}{99}
\bibitem{BaticDutykh2026}
D.~Batic and D.~Dutykh,
``Quasinormal Modes of Gauss--Bonnet Black Holes via the Spectral Method:
Scalar, Vector, and Tensor Perturbations,''
arXiv:2608.06083 [gr-qc] (2026),
\url{https://arxiv.org/abs/2608.06083}.
\end{thebibliography}
```
