# Validation record (A063 v0.2.0)

- Environment: Python/SciPy/NumPy FP64, SymPy polynomial reduction, Shapely 2.x crossing geometry.
- Full-run gate semantics: PASS is reference-level only; `T5` and `T6` FAIL are restricted to explicitly tested steady constructions. `T8`, `T9`, `T10` remain UNRESOLVED.
- Dedicated pytest regression suite includes independent trefoil construction, multiple projection directions, full numerical closure, zero-radius flux control, finite-radius leakage, sampled geometry, independent pointwise Beltrami relation, shear and tamper-detecting ledger hashes.
- Kinematic advection is convergence-checked using 384 and 720 surface markers. It does NOT imply nonlinear Euler or finite-core spectral instability.
- PDF and .tex report generated only from actual output JSONs, never relabel scientific gates.
- Native framework v1.0.7 FREEZE/CERTIFY: **NOT RUN**. No native C++ lane is implemented in this release; backend authority `REFERENCE_ONLY`.
- `SOURCE_SEAL.json` is an additive release-side source hash manifest, not a framework freeze/BLIND commitment. Historic v0.1.1 source and outputs remain untouched.
