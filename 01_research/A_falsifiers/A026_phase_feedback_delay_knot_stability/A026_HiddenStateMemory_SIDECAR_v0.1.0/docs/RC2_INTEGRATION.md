# SST Falsifier Framework v1.1.0 RC2 integration boundary

The connected Google Drive validation of SST_Falsifier_Framework_v1.1.0_RC2 dated 2026-10-28 labels the framework DEVELOPMENT / SOURCE-VALIDATED / TARGET-HARDWARE PENDING. Although 106 cross-platform framework tests and synthetic A999 integration tests passed, the real user's target hardware RC2 qualification and E010-v0.4.0 atlas admission remain pending.

This package is therefore deliberately **a portable diagnostic sidecar**, not a copied/stubbed Framework instance. It must not report official `FREEZE`, `FULL`, qualified G10, two independent science backends, or PDF publication certification.

If the user supplies the actual local RC2 template and E010-v0.4.0 source manifest, the migration path is:

1. Instantiate a new **approved A026 version** through the actual RC2 generator, after checking catalog_index.json and family_hierarchy.json for conflicts and registration.
2. Copy `configs/preregistered.json` and this scientific method into the generated instance's science_contract.json, source_contract.json, preregistration and report template, with predeclared Euler-specific gates and target thresholds.
3. Replace `src/model.py` surrogate by a real, source-free 3D Euler solver provider (plus a second independent C++ or Intel XPU backend, and optional third CUDA, evaluated through the native RC2 2-of-3 numeric parity gate).
4. Acquire independent, true physical nonintersecting finite-core trefoil/background trajectories from verified E010 and Ruban seed provenance. Reject equivalence between filament regularizer delta and Euler Gaussian width sigma.
5. Implement code-backed spatial/time/finite-core/box convergence, vortex invariants, material labels and matched-current / history-shuffle comparators. Test identical physical final time under time refinement.
6. Run the actual `pytest -q tests`, then official `run_all.cmd FREEZE`, `BASIC`, `FULL`, `CERTIFY` (if enabled), retaining all output roots. Only the source-owned framework may create canonical reports or qualify physical gates.
7. Do not promote Swirl Clock status unless phase carrier and independent operational tau measurement gates close.

No existing A026/A049/A068/A069/A075 code, Registry files, original datasets or frozen releases are modified by this sidecar.
