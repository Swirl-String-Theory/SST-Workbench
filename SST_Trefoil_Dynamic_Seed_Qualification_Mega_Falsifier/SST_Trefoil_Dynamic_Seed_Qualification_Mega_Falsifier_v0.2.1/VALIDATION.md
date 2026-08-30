# Validation — v0.2.1

## Correctness-release validation

- Python syntax compilation: **PASS**.
- Pytest methodology/regression suite: **20/20 PASS** using the local Windows v0.2.0 environment with the v0.2.1 source tree on `PYTHONPATH`.
- Historical `KnotPlot/knots/final` prepare: expected nonzero stop with `INDETERMINATE_INSUFFICIENT_SOURCE_DIVERSITY`; one eligible source group against the required three.
- Four-source real-geometry workflow smoke: S10–S60 and reveal executed; 4 source groups at S20, 3 S37-qualified smoke candidates, 2 S40 rows, 1 S50 row, 1 S60 row, and verified blind-key commitment.
- Smoke top-level physics verdict: **NOT_APPLICABLE_WORKFLOW_VALIDATION**.

The workflow smoke uses deliberately permissive thresholds and is not SST evidence. No new held-out scientific atlas was available, so v0.2.1 does not publish a new blind physics result.

Exact release-validation commands (PowerShell, from the v0.2.1 package root):

```powershell
$env:PYTHONPATH=(Resolve-Path 'src').Path
& '..\SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier_v0.2.0\.venv\Scripts\python.exe' -m compileall -q src tests
& '..\SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier_v0.2.0\.venv\Scripts\python.exe' -m pytest -q --basetemp 'C:\Users\oscar\Documents\Codex\2026-08-30\explore-x20\work\pytest-v021-release'
& '..\SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier_v0.2.0\.venv\Scripts\python.exe' -m sst_seed_falsifier.selftest
```

The fresh full smoke used the same interpreter and `PYTHONPATH`, `config\workflow_smoke.json`, the real four-file `Knot_Geometry_Library\SST_Knot_Geometry_Library_v0.1.1\outputs\seed_suite`, and these CLI commands in order:

```text
prepare, early, refine, resolution, temporal, core, mesh-gauge, long, rpo, mechanism, reveal
```

Release smoke output: `C:\Users\oscar\Documents\Codex\2026-08-30\explore-x20\work\v021-workflow-smoke-release`. Historical-source regression output: `C:\Users\oscar\Documents\Codex\2026-08-30\explore-x20\work\v021-historical-dataset-release`.

## Inherited v0.2.0 numerical regression record

## Static / unit validation

- Python syntax compilation: **PASS**.
- Original v0.2.0 pytest methodology/regression suite: **14/14 PASS** before packaging.
- Tests cover the v0.1.x JSON-null boundary, S40→S50 fail-closed behavior, source-stratified scheduling, parameterization-invariant shape comparison, tangential-only mesh velocity, temporal-gate behavior, mesh-gauge eligibility, and one-click script paths.
- Windows portability guard remains `py::ssize_t` in the native source.

## Native C++ / Python parity

The C++17/OpenMP pybind11 module was compiled and imported in the generation environment using the available pybind11 headers. Selftest:

```text
backend                  = cpp-pybind11-openmp
native_python_rel_l2     = 2.898329577875693e-17
self_alignment           = 5.650530578218433e-17
basis_dim                = 8
rolling_coherence        = 0.7478820566636595
PASS                     = true
```

The Linux test binary is deliberately removed before packaging; Windows builds its own `.pyd` with `run_01_build_native.cmd`.

The user's earlier Windows chain independently compiled the same native source family under MSVC/Python 3.14 and reached exact native/Python parity in that run before the old Python stage-boundary failure.

## Real v0.1.1 champion mesh regression

Regression geometry: `R5571B55051FC0A`, N=96, `dt_factor=0.025`, nominal core/physics, segment-feedback mesh controller.

- T=0.9: **COMPLETED**, max ds-CV `0.2555462520526713`, max mesh/physical RMS `0.28424778168517706`.
- T=1.2: **COMPLETED**, max ds-CV `0.2776792342204729`, max mesh/physical RMS `0.44682457515641005`.

Thus the v0.1.1 numerical stop around `t ~= 0.768` is surpassed on this regression shape without timestep coarsening.

### Mesh-gauge replay at T=0.9

| rate factor | status | max ds-CV | max mesh/physical | score | shape AUC |
|---:|---|---:|---:|---:|---:|
| 0.6 | COMPLETED | 0.3326512 | 0.2427549 | 0.7596946 | 0.0607052 |
| 1.0 | COMPLETED | 0.2555463 | 0.2842478 | 0.7647753 | 0.0604366 |
| 1.4 | COMPLETED | 0.2042413 | 0.3040495 | 0.7690857 | 0.0604013 |

Maximum pairwise final-shape distance was approximately `0.01711`. This is a numerical regression, not a blind scientific result.

## Temporal regression

For the same R557 geometry at N=96, T=0.35 and timestep factors 1, 1/2, 1/4, all runs completed. The final-shape discrepancies were approximately `2.51e-15` and `3.37e-15`, i.e. machine-floor limited. S32 therefore correctly uses its absolute-floor branch instead of reporting a meaningless observed convergence order.

## Full staged synthetic smoke

A three-source synthetic trefoil dataset was passed through S10→S20→S25→S30→S32→S35→S37→S40→S50→S60→S70 with deliberately permissive smoke thresholds. The chain completed and exercised source stratification, temporal certification, mesh-gauge certification, near-RPO/Floquet and material-vs-fixed mechanism code paths.

**This smoke is workflow validation only. Its PASS verdict is not SST evidence.**

## Known scope limitations

- regularized filament / finite-core surrogate, not volumetric 3-D Euler DNS;
- S50 is projected Floquet, not full tangent-space Floquet;
- S37 is a numerical gauge audit, not physical stabilization;
- v0.2.1 does not claim that the R557 regression geometry is the final physical trefoil champion.
