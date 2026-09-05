# Source Map and Authority

## Active authority used by this package

1. `source_material/SST_CANON-v0.8.34.tex`
2. `source_material/SST_CANON-v0.8.34-research-track.tex`
3. `source_material/deep_research_calibration_audit.md`
4. `data/ideal_favorites.txt`

## Canonical points carried forward

From MAIN CANON v0.8.34:

- symbolic mode should prioritize dimensionless spectra, ratios and scaling laws;
- calibrated-consistency outputs are not predictions;
- prediction mode requires unused observables and no retuning;
- dependency paths must be acyclic;
- a calibration input may not be counted again as a prediction;
- ideal-knot labels do not certify ropelength or dynamical stability;
- scalar ropelength is insufficient for shape-sensitive observables;
- the finite-cell \(\alpha\) relation is a sub-per-mille coincidence plus obstruction, not a ppm derivation.

From Research Track v0.8.34:

- finite-core energy and regularization must be declared;
- energy ratios must converge with vertex count, quadrature, kernel resolution and optimizer tolerance;
- relative-state solving is distinct from ropelength optimization;
- Floquet and KAM certification require the same operator in equilibrium, tangent and evolution stages;
- kernel dependence, topology loss and nonconvergent residuals are explicit falsifiers.

From the deep-research audit:

- no validated independent physical observable has yet been produced;
- dimensionless dynamics is the fastest route to one defensible prediction;
- dynamic knot residuals are genuine non-algebraic calculations;
- absolute mass and gravity programs remain calibrated or underdetermined;
- the old neutron/proton topology ratio fails;
- the local action selector is strongly core-profile dependent.

## Geometry source caveat

`ideal_favorites.txt` provides Fourier/AB centerlines and quoted geometric metadata. Its entries are initial geometric sources only. This package does not treat them as:

- exact ropelength minimizers;
- KKT-certified solutions;
- finite-core Euler states;
- particle states.

## v0.3.0 additions

- `src/sst_axial_vortex_bundle.py`: finite-radius continuum and discrete axial-bundle solver.
- `configs/B0_*.json` through `configs/B8_*.json`: preregistered ladder.
- `docs/07_axial_vortex_bundle_test_ladder.md`: mathematical gate definitions.
- `docs/08_physical_vs_numerical_tubes.md`: mode-separation rule.
- `docs/09_circulation_phase_clock.md`: clock-carrier diagnostic.
- `tools/analyze_bundle_modes.py`: fixed-total convergence and physical-flux audit.
