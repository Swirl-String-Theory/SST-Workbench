# Roadmap v0.3 — true physical mode solver adapter

Priority for the next release:

1. Define/import a declared SST centerline or finite-core energy functional `E[Q]` without fitting it to the desired spectrum.
2. Build the finite-difference/automatic-differentiation Hessian `H = d^2 E/dQ^2` about each relaxed knot.
3. Supply a physically justified generalized inertia/mass operator `M` and solve `H e_n = omega_n^2 M e_n` after rigid/gauge projection.
4. Convergence ladder over source geometry and perturbation step.
5. Controlled time-dependent encounters with before/after modal-energy projection.
6. Generate `amplitude_scan.csv`, `encounters.csv`, `convergence.csv`, and `energy_ledger.csv` directly rather than by manual transcription.
7. Add material-frame twist only when a material frame exists; add core modes only when a finite core is resolved.
8. Feed the resulting held-out physical dataset unchanged into the existing thermodynamic/spectroscopic falsifier.
