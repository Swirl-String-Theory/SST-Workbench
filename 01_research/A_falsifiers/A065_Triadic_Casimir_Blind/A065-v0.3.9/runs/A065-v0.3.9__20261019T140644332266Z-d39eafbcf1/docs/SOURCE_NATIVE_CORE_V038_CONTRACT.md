# A065-v0.3.8 — Source-Native Vorticity Core Closure (preparatory assay)

## Evidence boundary
**This version does NOT have a source-native Euler/PKLSA vorticity field.** The static E010/E011 source geometry is used as an initial centreline, with a *chosen* dimensionless Gaussian smoothing width. It cannot determine the true SST core. All synthetic-field data are labelled `GEOMETRY_DERIVED_SYNTHETIC_3D_NOT_PKLSA_EULER`.

## 1. How to obtain a genuine PKLSA source
Export `omega(x,y,z,t)` or `u(x,y,z,t)` **from a separately qualified finite-core Euler/PKLSA dynamic solver**, with grid axes/dx and SI or dimensionless units, density, real boundary conditions, physical initialization and time, source hash, solver git revision, core initialization prescription, and several time snapshots. Do not infer omega from XYZ centreline without stating your arbitrary smoothing hypothesis. Time-independent geometry XYZ files are never a volumetric dynamic source. The Google Drive E010/E011 status currently establishes static preparation only.

## 2. Local normal sections
For each precommitted curve station compute t, e1, e2; then evaluate normal-field omega_parallel = omega dot t. Define Gamma(Sigma)=integral omega_parallel dA and Z(Sigma)=integral omega_parallel^2 dA. Flag cancellation |integral omega_parallel|/integral |omega_parallel|<0.8, nonaxial component fraction>0.5 and tiny net Gamma <0.25. These limits are diagnostic; source dynamics may justify alternative preregistration only in a NEW release.

## 3. Zero-holdout-fit inversion
Under Gaussian 2D vortex cross-section assumption, derive `a=abs(Gamma)/sqrt(2*pi*Z)`; for uniform Rankine profile instead `a=abs(Gamma)/sqrt(pi*Z)`. The 3D Gaussian source in v038 uses a prescribed a as synthetic ground truth. Neither a nor epsilon is measured from the historical XYZ. The putative Rosenhead cutoff requires an *extra* matching definition (e.g. near-axis slope vs half-circulation). Report that ambiguity separately.

## 4. Independent holdout
To test physical predictions, acquire u and p from an independently computed physical solver/diagnostic provider, preserve separate source hashes and blindness, and compare only after a, Gamma, model type and epsilon mapping have been frozen. The v038 FFT u/p is calculated from the generated omega, thus **dependent surrogate data**, not an independent physical holdout. Periodic pressure Poisson does not imply a steady Euler solution; inspect the momentum residual.

## Gate meanings
- G28: 3D field / div(u), pressure Poisson code diagnostics, synthetic only.
- G29: all cross sections meet contamination/admissibility tests (expected failure possible).
- G30: a Gaussian-conditional a computed with no u/p fit on >=1 admissible station per source.
- G31: Gaussian heldout dependent numerical u/p model prediction at <=5% for each admissible station (negative result retained).
- G32: independent authentic 3D PKLSA Euler snapshot and heldout provider (UNRESOLVED until external evidence).

The 11 legacy sealed source files and all historical gate outcomes are immutable. No reveal. No physical Casimir or gravity promotion.

## Native velocity conversion tool
`tools/convert_native_velocity_v038.py` accepts a separately produced source-native periodic 3D velocity grid, checks source SHA256, computes omega with a spectral curl and emits a new NPZ and audit. This does not independently certify the solver or any heldout provider. Never reinterpret the standalone synthetic `CORE3D` output as a native solver result.
