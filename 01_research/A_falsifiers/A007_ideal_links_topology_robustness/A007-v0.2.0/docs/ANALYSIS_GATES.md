# Analysis gates v0.2.0

## G0 — source integrity

- XML parsing succeeds.
- All 18 preregistered link IDs exist.
- Component count, declared length and coefficient ranges are recorded.
- Input SHA-256 is written to every campaign metadata file.

## G1 — Fourier reconstruction

\[
\mathbf r(t)=\frac{\mathbf A_0}{2}
+\sum_{n\geq1}\left[\mathbf A_n\cos(nt)+\mathbf B_n\sin(nt)\right].
\]

The first three derivatives are analytic. Periodic closure, integrated length and spectral-tail convergence are checked.

## G2 — geometric structure

- length and radius-based ropelength;
- curvature and torsion distributions;
- total curvature and bending integral;
- inertia, planarity, axisymmetry and area vector;
- inter-component length imbalance.

## G3 — topology

- C++ Gauss-linking matrix;
- integer-lock error;
- NumPy/C++ parity;
- component writhe proxy;
- rigid-motion, mirror and orientation reversal identities.

## G4 — contacts

- refined mutual minimum distance;
- diameter-contact coverage;
- nonlocal self-distance proxy;
- contact graph and cycle rank.

## G5 — circulation sectors

Every \(\sigma_i\in\{-1,+1\}\) assignment is evaluated. Two-component links have four sectors; three-component links have eight.

## G6 — native Biot–Savart

- C++17/pybind11 midpoint-segment kernel;
- OpenMP when available;
- self-segment exclusion;
- multiple soft-core radii;
- Python reference parity before production.

## G7 — relative equilibrium

The normal component of the velocity is fitted to a common rigid translation and rotation. Tangential velocity is treated as centerline reparametrization.

## G8 — provenance and convergence

- resolution ladders;
- softening ladders;
- backend and compiler metadata;
- C++ source hash;
- input hash;
- result-signature-aware resume.

## Interpretation guard

A small residual is a candidate geometric/dynamical regularity, not automatically an SST particle prediction. Finite-core closure, circulation orientation and physical normalization remain separate gates.
