# Source-to-gate map

Primary source: Dubovsky, Hui, Nicolis & Son, arXiv:1107.0731 / Phys. Rev. D 85, 085029 (2012).

| Paper structure | Paper equation(s) | Falsifier use | Status |
|---|---:|---|---|
| Comoving material scalars `phi^I` | (1)-(2) | arclength/material-label treatment | source-derived concept |
| Internal translations/rotations + volume-preserving relabeling | (3)-(5) | G1 relabeling surrogate | source-derived symmetry; centerline surrogate is SST implementation |
| Chemical shift `psi -> psi + f(phi^I)` | (8) | G2 gauge-shift test | source-derived symmetry; Bishop phase is SST candidate |
| Identically conserved material current `J^mu` | (10)-(13), (33) | motivation for material-coordinate invariants | source-derived |
| Leading action `S = integral F(b,y)` and `y=u^mu partial_mu psi` | (15)-(16) | comoving phase-rate motivation | source-derived; SST phase-clock interpretation is extrapolation |
| Higher-derivative expansion | Sec. IV | G3/G4 operator hierarchy | source-derived method |
| Sample second-order term | (61) | motivation for explicit higher-gradient basis | source-derived example |
| Quartic dispersion correction | (73) | G4 target form `omega^2=a2 q^2+a4 q^4` | source-derived form; vortex-mode application is SST extrapolation |
| Redundant couplings removable by field redefinition | (75)-(83) | G3 redundancy pre-gate | source-derived principle |

## Deliberate limitations

- A static knot centerline is **not** a full 3D material-coordinate field, so G1 cannot test the complete volume-preserving-diffeomorphism symmetry.
- A static knot centerline does **not** contain a measured physical `psi`; G2 tests a geometric holonomy candidate only.
- G3 can decide total-derivative and integration-by-parts redundancy from centerline data. EOM/field-redefinition redundancy needs a specified leading SST action.
- G4 uses a regularized finite-core Biot-Savart filament closure. It is not full 3D Euler.
