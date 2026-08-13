# v0.3.3 continuum bridge to v0.4

The v0.3.2 full campaign showed that a fixed number of omitted self-segments is not a continuum-safe
regularization.  v0.3.3 replaces that choice in the QM presets by a fixed physical arc exclusion.

## Gate C1 — regularization held fixed under refinement

For every component, segment midpoints are assigned polygonal arclength coordinates.  A self pair is
excluded when the minimal cyclic arclength separation obeys

\[
\Delta s_{\rm cyc}\le s_{\rm excl}.
\]

`self_exclusion_energy_arc_D` and `self_exclusion_velocity_arc_D` are dimensionless fractions of the
Gilbert diameter `D`.

## Gate C2 — N convergence

`run_continuum` evaluates length, bending, repulsion, Neumann energy and relative-equilibrium residual
at a sequence of N values.  The final two grids are compared directly.  Richardson extrapolation is
reported only when three factor-two grids give a monotone-sign error sequence.

## Gate C3 — no cross-grid calibration constants

QM energy terms are D-dimensionalized rather than divided by medians taken from another run.
Profile weights remain assumptions and are the object of the v0.4 closure-simplex scan.

## Gate C4 — stationary probe before stability interpretation

The full-Hessian best sector receives a local Newton probe.  A Hessian at a nonstationary source
geometry remains a local curvature diagnostic, not a physical normal-mode stability operator.

## Gate C5 — singular two-form handling

The SVD kernel of the candidate two-form is recorded explicitly.  An image-space quotient is supplied
for algebraic diagnostics, but the release refuses to identify that quotient with the physical phase
space until an action-level derivation classifies the kernel.

## Borromean dependency

For `L6a4`, pairwise Gauss linking is zero and the catalog identity is Borromean rings.  The catalog
value `|mu-bar_123|=1` is recorded as external identity metadata.  A numerical Milnor implementation
remains a separate dependency and must not be conflated with the catalog lock.
