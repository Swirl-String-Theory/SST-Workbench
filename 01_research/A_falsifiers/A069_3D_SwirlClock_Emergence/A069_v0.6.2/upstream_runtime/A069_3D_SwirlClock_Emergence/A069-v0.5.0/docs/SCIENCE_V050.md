# A069 v0.5.0 — 3D GP trefoil dynamics (development)

**Scope**: real three-dimensional compressible GP evolution of solid-angle/winding initialized historical 2015 trefoils on 48^3 and 64^3 grids. This is **not** an incompressible Euler run, not a stable knotted-particle certification and not an independently measured Swirl Clock.

**Independent frequency result**: Bogoliubov dispersion of a **homogeneous reference state** predicted analytically, tested by an FFT-derived and independent nonlinear time-domain mode fit over >9 cycles. This is **not** a trefoil eigenmode. The knot's 3D BdG tangent-response JVP matches finite differences but requires a stationary/reduced-periodic knot before a Floquet eigenfrequency is physical. G29--G31 remain UNRESOLVED.

**Source policy**: original 2015 parameterized A and B XYZ are SHA-pinned and reconstruction-verified. Exact mirrors are correlated controls. KnotPlot visually relaxed geometries remain excluded. STATIC_READY E011 does not imply DYNAMICS_READY.

**Frozen source integrity**: `science_contract.json` SHA-256 pins `configs/GP3D_CAMPAIGN_V050.json` plus every `experiment/*.py` file. Source manifest must report all inputs with `exists=true` and correct bytes before accepting a run.

**Environmental**: Python NumPy/SciPy FP64 with Numba CPU initializer. Shared framework must be the locally installed official v1.0.9 at 06_templates; `.sst_framework_root` points there, fail-closed. No native C++/SYCL hardware certification.

**Windows**:

```bat
python -m pip install numpy scipy numba pytest
python -m pytest -q tests
run_all.cmd FREEZE
run_all.cmd BASIC
run_all.cmd REPORT_ONLY
run_all.cmd REVEAL_IF_ALLOWED
```

FULL/CERTIFY are *not* enabled as physics qualification; absence of independent observations must never become PASS. Do not rerun FREEZE after any source/contract edits; create v0.5.1.

**New gates**: G26 initial-value 3D GP, G27 independent bulk Bogoliubov, G28 tangent BdG model validation, G29 trefoil intrinsic eigenmode, G30 stable fully qualified 3D knot physics, G31 A061/physical clock closure.

**Production next**: develop vortex-filament extraction + topology tracking across time, long-run convergence, genuine stationary relative knot/periodic orbit and then shape-reduced Floquet mode predictions on independent providers.
