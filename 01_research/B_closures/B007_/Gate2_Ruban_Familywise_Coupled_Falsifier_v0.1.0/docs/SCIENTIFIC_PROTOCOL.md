# Four-gate scientific protocol (precise limitations)

## G1: Geometric seed preflight
Original analytic torus embeddings are used verbatim. The radius `B0` in E010 is the torus minor radius over the major radius, **not** the finite-core vortex radius `aK`. A polygon may be geometrically closed and knot-like but fail finite-core nonintersection; an index-exclusion proximity check is not a rigorous reach bound. Perturbation topology remains unproved until certified.

## G2: Fast dynamical prescreening
Regularized vortex-induction midpoint segment approximation:

`u_i = Gamma/(4*pi) * sum_j Delta X_j cross (X_i - M_j) / ( |X_i - M_j|^2 + exp(-2*Lambda) )^(3/2)`.

This is not an exact Biot-Savart line integral; it models infinitesimal filament segments. The short Heun step tests whether apparent stationarity is not immediately an artifact of the initial point. It cannot imply long-term stability; the relative shape-velocity residual normalizes by the actual induced speed, and values near vanishing velocity require special treatment.

Both original and deterministic E010 perturbation undergo the same calculation. G2 does not simulate background vortices.

## G3: Holdout & ranking
One `B0` selected **within** each of twelve embedding families; global ranking is explicitly provisional, not an experimental winner. New filament samplings 128/256/512 (screen N=192) check discretization changes. Separate true numerical-convergence and material topology checks remain required.

## G4: One or more *live* background loops in Euler
Every component shares `u_total = K_periodic[sum_alpha omega_alpha]`. Each material component evolves via `d_t omega_alpha = curl(u_total cross omega_alpha)`; no background is frozen in physical coupled runs. Gaussian-smoothed closed curves imply globally solenoidal vorticity (before spectral alias filtering), zero mean vorticity in the periodic box, and noncompact analytic Gaussian tails. The background loop has an initially vertical central branch and a remote return branch; the extended grids have a known close-contact/crossing risk from the chosen return geometry and are INVALID as independent physical vortex tubes until re-routed with proven disjoint closure. Sampled-vertex proximity checks are preflight only, not continuum segment/finite-radius proofs. The periodic cube includes periodic images and cannot realize arbitrary continuously rotating rigid z-frame equilibria, so only U_z is fitted.

An independent holdout is evaluated at fixed U_z without refitting, at n24 versus n20 (same spectral implementation). It is a partial numerical check and does **not** demonstrate continuum convergence. Stronger G4 gates need: much higher resolution relative to sigma; distinct Biot-Savart backend; free-space/axisymmetric boundary model; constant common final time step studies; full isovortical field optimization; rigorous knot tube isotopy/flux preservation; and nontrivial zero residual.

## Falsification criteria
- A large nonzero G4 fixed-U holdout Euler residual: **no equilibrium certification**, though does not prove universal nonexistence.
- Negative or vanishing velocity normalization: report raw residuals and avoid favorable ratios.
- Any topology collision or unresolved overlapping cores: halt physical claims; record numerical issue.
- No spatial/temporal/solver parity: remain `UNRESOLVED`.
- Filament loop kinetic energy and helicity are **not** closed-system energy invariants without a consistent domain/model.

## Literature boundaries
Enciso and Peralta-Salas prove existence of knotted invariant tubes in infinite-energy globally decaying Beltrami Euler fields, not the present compactly supported isolated trefoil plus lattice. Cao, Lai, Qin, Zhan and Zou establish stability in a special axisymmetric ring class, not knotted 3D network stability.
