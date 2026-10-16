# A062 — SST Microgravity Force-Gradient Falsifier v0.1.0

**Scientific status: MODEL-SPECIFIC TEST, NO EXPERIMENTAL SST CERTIFICATION.**

- Reference: Zhu et al. (2026), Nature Nanotechnology, doi:10.1038/s41565-026-02298-8.
- Instances belong under `SST-Workbench/01_research/A_falsifiers/A062_sst_microgravity_force_gradient/A062-v0.1.0/`.
- Framework: **SST_Falsifier_Framework_v1.0.7** (`CANONICAL_FROZEN`), referenced by `.sst_framework_root`. It is **not bundled or modified**.
- `run_all.cmd FREEZE`, `BASIC`, `FULL`, `CERTIFY` call the **pinned framework** and fail closed if it is absent.
- `run_science.cmd` (or `python -m microgravity.runner BASIC`) runs a **standalone scientific diagnostic**, independent of the installed framework. This is NOT a substitute for v1.0.7 certification.
- `python -m unittest discover -s tests -v` runs local unit/invariant tests.
- `run_science.cmd FREEZE` records a local source SHA-256 protocol commitment; it never replaces the v1.0.7 protocol freezer.
- `run_science.cmd BASIC` computes analytic Newton reference and Gaussian Euler-Poisson surrogate, without trying to fit the measured target.
- `run_science.cmd FULL` adds grid refinement, all seven gates and report generation.
- `run_science.cmd CERTIFY` requires compiled C++ FP64 parity of hydrodynamic gradient, failing closed when compilation/toolchain is absent.
- All gates run despite earlier failures. `UNRESOLVED` is preserved when independent experimental data are unavailable.
- Output resides in `A062_SST_Microgravity_Force_Gradient_v0.1.0-outputs` inside instance; packaged beside the instance as `_BLIND.zip`. The local standalone report PDF is written to the parent too when LaTeX is available.

## Physics scope

Hypothesis H0 is Newton's force and gradient with the published masses/distances (calibration comparator; published force figures cannot infer G independently). H1 is *one* tightly constrained localized Gaussian azimuthal vortex field with exact divergence-free initial velocity and Euler pressure-Poisson source (not an established stationary solution or knot). The pressure-gradient force assumes a small material volume `Vt=4*pi*a^3/3`, which is a **test proxy**, not the experimental 100 g pendulum body. Mass mapping is *explicitly speculative* `E_kin/c^2`; no data-driven fit and no imported G in the H1 calculation. FAIL falsifies this restricted H1 closure only; neither falsifies SST in general nor tests a full PKLSA knotted geometry.

For a proper blind physical validation, acquire independent calibrated source-mass / test-mass separation sweeps with raw time series, apparatus mechanical transfer function and uncertainty budget. Integrate a genuine PKLSA core/finite-core source provider only under a new preregistered release.

The original user-provided Nature Nanotechnology PDF is bundled under `inputs/s41565-026-02298-8.pdf`; no supplemental raw measurement traces are bundled or implied.
