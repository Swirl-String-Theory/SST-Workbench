# Analysis gates

The campaign deliberately separates exact/source checks, numerical diagnostics and SST Research-Track lifts.

## G0 — source integrity

- XML parse succeeds.
- All 18 requested IDs exist.
- Component count, declared length and coefficient range are recorded.
- SHA-256 of `idealLinks.txt` is written to `run_metadata.json`.

## G1 — Fourier reconstruction

For each component,

\[
\mathbf r(t)=\frac{\mathbf A_0}{2}
+\sum_{n\geq1}\left[\mathbf A_n\cos(nt)+\mathbf B_n\sin(nt)\right].
\]

The suite evaluates the first three derivatives analytically and checks periodic closure.

## G2 — geometry

- Numerical and declared centerline lengths.
- Gilbert \(L/D\) and standard radius-based ropelength \(2L/D\).
- Curvature, torsion, total curvature and bending integral.
- Inertia tensor, planarity, area vector and spectral convergence.

## G3 — topology

- Pairwise Gauss-linking matrix.
- Integer-lock error.
- Component writhe proxy when enabled.
- Translation, proper-rotation, mirror and orientation-reversal identities.

## G4 — contacts

- Refined inter-component minimum distance.
- Diameter-contact coverage.
- Nonlocal self-distance proxy.
- Contact graph, degree and cycle-rank diagnostics.

## G5 — circulation sectors

Every component circulation assignment \(\sigma_i\in\{-1,+1\}\) is evaluated.
This gives four configurations for two-component links and eight for three-component links.

## G6 — regularized Biot–Savart dynamics

- Centerline velocity.
- Best normal rigid translation/rotation.
- Relative-equilibrium residual.
- Geometric impulse.
- Regularized Neumann energy proxy.
- Core-softening convergence.

## G7 — comparative catalogue

- One common feature table.
- Rankings, correlations and PCA.
- Outlier discovery across all 18 links.
- `--all-database` extends the same protocol to all 130 links in the supplied source.

## Interpretation guard

A small residual is not itself a physical prediction. Contact cycles, mirror scores, regularized
energy and SI lifts remain diagnostic until the governing finite-core closure, circulation assignment
and boundary conditions are independently fixed.
