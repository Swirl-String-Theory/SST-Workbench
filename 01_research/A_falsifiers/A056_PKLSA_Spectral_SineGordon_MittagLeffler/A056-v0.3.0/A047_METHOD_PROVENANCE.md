# A047 method provenance for A056-v0.3.0

The volumetric `euler_ps3d` provider is an instance-local adaptation of the already audited A047-v0.3.0 E010/Euler route. A056 does not import A047 at runtime and does not inherit any A047 verdict. The relevant A047-v0.3.0 manifest hashes inspected before this release were:

- `sst_bkm/pklsa.py`: `bc9eaab4cc853e48a7384b6d23f8726c2eaf1bdac9891da71fa2a064d26f0131`
- `sst_bkm/spectral.py`: `7caa6ed54ef17d2ec3f80c9a5eab26685caa9a4aa698f1ae7c0ba779d26f0131`
- `sst_bkm/seed.py`: `f177e29ad0f6697ffdffd33c8b67e65f76bc712d01af46fe325defb33efe914f`
- `cpp/native.cpp`: `a90f97ef4431ceff4cbc24d36a777983de8417c813b4957321d38c1c1d91703f`

Adapted method elements: E010-v0.3.1 source-native admission and hash verification, Gaussian tangent vorticity tube, Fourier solenoidal projection, 2/3 dealiasing, velocity-vorticity Euler RHS, and RK4 time stepping. A056 adds paired material-marker transport, a frozen Kelvin perturbation, Bishop-frame phase extraction, projected mode envelope, and A056-specific model competition.
