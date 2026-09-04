# Changelog

## v0.1.1 — 2026-08-07

- Bundled and parsed the user-supplied Brian Gilbert `Ideal.txt.gz` and `IdealLinks.txt.gz` databases.
- Implemented Gilbert Fourier sampling, including the `A[0]/2` constant-term convention.
- Reproduces source ropelength sampling conventions: 512 points for knots; 256/128 per link component according to component count.
- Added optional `sst_core` scaling: database tube diameter `D=1` maps to physical diameter `2*r_c`.
- Added multi-component finite-core energy and Biot–Savart kernels in both C++ and Python fallback; link strings are never spuriously joined.
- Added Gauss-linking audit for multi-component records.
- Added `run_ideal_database.py`, Ideal.txt/IdealLinks options in `run_drift_scan.py`, and Windows quick/full-catalog `.cmd` runners.
- Added catalog/parser, Fourier reconstruction, topology, physical scaling, and multi-component parity tests.


## v0.1.0 — 2026-08-07

- Adapted the standard SST C++/Python pybind11 audit template.
- Added regularized finite-core filament energy and Biot-Savart velocity kernels in C++ and Python.
- Added Galilean uniform-drift baseline and `chi0/chi2` fit.
- Added synthetic sensitivity recovery control.
- Added generic `q/m` universality and dipole mismatch gate.
- Added homogeneous linear incompressible-Euler no-bulk-wave structural test.
- Added far-field flux / radiation-reaction energy-balance closure gate.
- Added PSR J1738+0333 corrected `Pdot_b` reference gate.
- Added effective preferred-frame observational gate without assuming an SST-to-PPN identity.
- Added internal controls, pytest suite, JSON/CSV outputs, manifest/checksums workflow.
