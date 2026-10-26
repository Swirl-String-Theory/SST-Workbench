# Ruban-family independent falsification matrix

| Branch | Independent variable | Measured objective | Status |
|---|---|---|---|
| Ideal / tight geometry | shape under fixed knot type and thickness convention | `Rop=L/(2*reach)` or independent ideal benchmark | NOT_EVALUATED |
| Ruban torus geometry | `p,q,B0`, core `Lambda`, regularization `delta`, initial perturbation | source-native initial conditions | GEOMETRY_GENERATED |
| Regularized induction dynamics | same seed in fixed solver, `Gamma`, `xi`, local correction and timestep | deformation survival time with censoring | NOT_RUN |
| Euler finite-core cross-model | equal physical initial vorticity and kernel/circulation normalization | survival/conservation vs Ruban model | NOT_RUN |
| Topology robustness | embedding, core resolution, perturbation modes | ambient-isotopy proxy plus minimum separation, independent knot certificate | NOT_EVALUATED |
| Model comparison | `B_ideal`, `B_dyn`, uncertainty intervals | overlap / disjointness / unresolved | NOT_EVALUATED |

Decision rules: a fitted geometric proxy is not a verified ropelength. `NO_WINDOWS_IN_SCANNED_DOMAIN` is evidence on the original source's parameter/model regime only, not an absolute impossibility theorem. `QUASISTABILITY_WINDOWS_REPORTED` is a source-claim label, not a passing new simulation. The same analytic torus-knot generator at many B0 points counts as ONE provenance group. An overall PASS requires both a validated geometric baseline and a converged dynamical run; independently qualified geometry can still be dynamically unstable.

For Ruban-like replication use characteristic dimensionless `Gamma=2*pi`, `R0=1`, `Lambda=ln(R0/xi)`, and distinguish `delta` smoothing from core width. In the paper simulation employs spectral representations and fourth-order time integration. Do not blindly set `Lambda0=0` for a different regularization kernel; preserve the total logarithmic local-induction correction.

For a survival-time gate choose a documented deformation threshold and fixed maximum observation horizon; model non-failure at that horizon as right-censored, not as proof of permanent stability. Separate convergence in N, dt, regularization, kernel and perturbation amplitude.
