# A075 v0.2.12 delta

- Added free 2N-normal-displacement Newton–Krylov solver (no Fourier shape-family restriction).
- Added explicit tangent parameterization projection, two axial symmetry phase gauges and simultaneous U/Omega unknowns.
- Added finite-difference JVP, GMRES, right numerical FFT preconditioner, safeguarded backtracking.
- Added optional Numba acceleration with strict parity against SciPy/NumPy reference.
- Added progressive mesh continuation and untouched-shape 2N plus midpoint holdouts.
- Added separate per-N displacement/XYZ archives, source/config manifests and automated PDF+Markdown falsifier report.
- Frozen A007 seed and original A075-v0.2.9 source retained byte-identically. v0.2.11 code retained for regressions and provenance.
- NO physical stability, exact continuum equilibrium, topology or spectral gates promoted.
