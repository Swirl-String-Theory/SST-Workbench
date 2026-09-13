# CHANGELOG

## v0.3.3 — Periodic-Cubic Remap Closure Hotfix

- Corrects a preregistration/implementation mismatch in v0.3.2: S37C documented periodic-cubic arclength remapping but executed polygonal linear `np.interp` remapping.
- Adds `resample_closed_periodic_cubic`: periodic `CubicSpline` interpolation followed by dense spline-arclength inversion.
- Preserves the first-marker cyclic phase anchor exactly.
- Uses the periodic-cubic discretisation for the S37C resolution ladder and the same frozen map in S40, S50 and Phase B.
- Keeps the legacy polygonal-linear remapper only as an explicit diagnostic kernel (`legacy_linear`); it cannot be selected silently.
- Adds remap-kernel identity and oversampling parameters to the frozen dynamics contract.
- Does not loosen any S37C final-shape, score-span, AUC-span or convergence-order threshold.
- `chi_eff` remains target-free and diagnostic-only.

## v0.3.2 — Operator-Split Arclength Remap + Target-Free Shape Ratio

- Added S37C prospective operator-split remap certification.
- Physical RK4 stages contain no tangential mesh-controller velocity.
- Uniform-arclength remap occurs only at frozen physical times.
- S37A and S37B remain unchanged historical/diagnostic comparators.
- S40 admission moves to S37C for this release.
- S40 and S50 use the same `SST-TREFOIL-DYNAMICS-CONTRACT-2` map.
- Added target-free `chi_eff = R_radial/r_axial` trajectory observable; it never enters scoring or promotion.
- Added spatial convergence requirement for remap-cadence sensitivity.
- Updated Phase B to the same operator-split map and replaced the old mesh-rate ladder with a remap-interval ladder.
- Output convention retained with separate BLIND and REVEALED archives.

## v0.3.1

Mesh-gauge closure diagnostic S37B; legacy continuous tangential controllers retained in S37A.
