# Changelog

## v0.1.2 — 2026-08-07

### Purpose

Numerical hardening release between the v0.1.1 convergence audit and
the planned v0.2.0 ideal-trefoil / relative-equilibrium campaign.

v0.1.1 established:

- implementation/null-model checks PASS;
- matcher self-overlap ≈ 1;
- trefoil scalar-energy convergence reaches ~0.122% for N=48 → 64;
- only 2/96 trefoil matched groups passed the v0.1.1 convergence gate;
- several oscillatory branches show stable frequency/circularity but weak
  individual-vector overlap;
- the default core scale is still insufficiently resolved at moderate N.

### Added

#### Core-resolution gate

\[
\eta_a =
\frac{\max_j\Delta s_j}{a}.
\]

Classification:

- `RESOLVED`: \(\eta_a\le0.5\)
- `DIAGNOSTIC`: \(0.5<\eta_a\le2\)
- `UNDERRESOLVED`: \(\eta_a>2\)

#### Two distinct degeneracy scales

- `TRUE_DEGENERACY_TOL`
  - used for circularity diagonalization inside a genuine eigenspace;
- `MATCHING_CLUSTER_TOL`
  - used for N→N' mode tracking of numerically split near-degenerate
    branches.

#### Near-degenerate subspace matching

Mode identity is now based on principal angles between eigenspaces rather
than only individual eigenvectors.

#### Arclength Fourier fingerprints

For every ring and trefoil mode:

\[
P_m =
\left|
\int q(s)e^{-2\pi i m s/L}\,ds
\right|^2.
\]

Fingerprints are used as an independent matching observable.

#### Eigenvalue conditioning

Left and right eigenvectors are used to compute

\[
\kappa_i =
\frac{\|x_i\|\|y_i\|}
{|y_i^\dagger x_i|}.
\]

Large \(\kappa_i\) flags modes whose eigenvectors may rotate strongly under
small discretization perturbations.

#### Separate interpretation gates

v0.1.2 distinguishes:

1. `implementation_ok`
2. `numerical_tracking_ready`
3. `physical_interpretation_ready`

A numerically trackable mode is not physically interpretable unless its
core discretization is also `RESOLVED`.

#### Resolution ladder

Presets:

- `quick`: 48,64,96
- `full`: 64,96,128
- `max`: 128,192,256

### Changed

Convergence matching now combines:

- principal-angle subspace overlap;
- relative frequency drift;
- circularity-spectrum drift;
- arclength Fourier-fingerprint similarity;
- cluster dimensional consistency.

The frozen torus trefoil remains diagnostic only.

### v0.2.0 gate

v0.2.0 requires:

1. resolved core sampling;
2. stable subspace convergence;
3. imported ideal-trefoil centerline;
4. relative-equilibrium/co-moving-frame solution;
5. rigid/tangential gauge removal.

---

## v0.1.1

Added:

- dimensionless mode frequencies;
- mode classification;
- ring Fourier identity;
- N→N' matching;
- principal-angle overlap;
- degenerate-subspace circularity;
- explicit physical-interpretation gate.

Audit result:

- baseline PASS;
- physical_interpretation_ready = false;
- trefoil N48→N64 energy convergence ≈ 1.22×10^-3;
- 2/96 matched trefoil groups passed.

---

## v0.1.0

Initial null-model implementation:

- finite-core Biot-Savart;
- analytic Fréchet derivative;
- Python/C++ parity;
- circulation reversal;
- mirror-energy degeneracy;
- frozen transverse eigenspectrum;
- circularity observable.
