# SST-Workbench inventory

Snapshot date: **2026-08-04**.

This is a full-tree inventory of the Workbench. It complements (and in places corrects)
[README.md](README.md) and [WORKBENCH_LAYOUT.md](WORKBENCH_LAYOUT.md).

| Companion document | Contents |
|--------------------|----------|
| [INVENTORY_FALSIFIERS.md](INVENTORY_FALSIFIERS.md) | Master falsifier registry (5 families; physics vs numerics) |
| [INVENTORY_PYTHON.md](INVENTORY_PYTHON.md) | Research / calculation Python scripts by pack |
| [INVENTORY_ARCHIVES.md](INVENTORY_ARCHIVES.md) | Zip archives (centralized under `Restore_Archives/`) |
| [INVENTORY_DUPLICATES.md](INVENTORY_DUPLICATES.md) | Nested / duplicated working directories and copies |
| [Restore_Archives/README.md](Restore_Archives/README.md) | Theme layout + consolidate script usage |

## What this repository is

SST-Workbench is the **research sandbox** for Swirl String Theory. It is **not** the
canonical source of SST definitions.

| Repository | Role |
|------------|------|
| SwirlStringTheory | Canonical theory (`papers/SST-CANON/`) |
| SSTcore | Stable Python/C++ API (`pip install SSTcore`) |
| **SST-Workbench** (this repo) | Versioned research packs, dashboards, pipelines, migration archive |

Measured baseline (excluding `.git`):

| Quantity | Value |
|----------|------:|
| Directories | 4160 |
| Tracked content (approx.) | ~11.9 GB |
| Hidden `.tmp.driveupload` | 4.4 GB / 9051 files |
| Python files (excl. `.venv` / caches) | 1528 |
| Of which `test_*.py` | 108 |
| `pyproject.toml` / `pytest.ini` / `conftest.py` | 23 |
| Archives (`.zip` etc.) | **563 under `Restore_Archives/` (~2406 MB)** as of 2026-08-24 |
| Archives with an extracted sibling folder | See [INVENTORY_ARCHIVES.md](INVENTORY_ARCHIVES.md) (bundles = theme zip + pack tree) |
| Archives never unpacked here | See [INVENTORY_ARCHIVES.md](INVENTORY_ARCHIVES.md) |
| Python scripts that exist **only** inside archives | 13 (paths now under `Restore_Archives/`) |

## Where README / WORKBENCH_LAYOUT are stale

| Claim in existing docs | Actual state (2026-08-04) |
|------------------------|---------------------------|
| `to_be_processed/` holds chi-phase / horn / routes packs | Stub only: one `README.md` pointing at relocated roots |
| `verification-suites/` described as a suite tree | One file: `embedded-knots/test_embedded_knots.py` |
| `experiments/derive_constants/` and `experiments/trefoil/closure/` as content homes | Stub READMEs only; real content at root research folders |
| `experiments/` as general experiment home | Three SYCL `.cpp` probes under `experiments/sycl/` plus stubs |
| Layout table omits several root packs | Missing e.g. `SST_fermat_pybind_research`, `SST_contact_billiard_hydrodynamic_falsifier`, `SST_dimensionless_dynamic_predictions`, `SST21D_knot_order_pipeline`, `SST_Sutcliffe_HSS_feasibility_gate`, `SST_minimal_falsification_harness`, `KnotPlot`, `KnotTheory` |

## Top-level directory map

Sizes and file counts from a recursive scan (2026-08-04). Kind: **code** / **data** / **output** / **tooling** / **stub** / **vendored**.

| Directory | Size (MB) | Files | Kind | Role |
|-----------|----------:|------:|------|------|
| `KnotPlot/` | 5354.1 | 7059 | code+output | KnotPlot ↔ ridgerunner pipeline; dominates disk via `ridgerunner/out/` and `knots/` |
| `3D/` | 2589.1 | 192 | code+data | Coil / gear / mold STL generators and slicer outputs |
| `media/` | 1459.3 | 32422 | data | Images, presentations, voiceovers, VAM illustration scripts |
| `SST_fermat_pybind_research/` | 706.7 | 1717 | code | Fermat-metric / Biot–Savart knot diagnostics (v0.1–v0.6.1) |
| `proof-scripts/` | 487.8 | 1119 | code | SSTcore examples + swirl VAM / proof / simulator trees |
| `SST_contact_billiard_hydrodynamic_falsifier/` | 365.9 | 9336 | code+output | Contact-billiard hydrodynamic falsifier (incl. nested `.venv` ~280 MB) |
| `SST_dimensionless_dynamic_predictions/` | 279.4 | 7296 | code+output | Dimensionless knot dynamics / C9 iso-Γ/A falsifier |
| `datasets/` | 235.9 | 3155 | data | SPARC, paper zips, gravity/swirl visualizers |
| `SST_Trefoil_Closure/` | 182.7 | 1323 | code+output | Merged trefoil closure + robustness sweeps + early chi-phase v1–v6 |
| `SST_routeB_RT_bem_research/` | 154.3 | 12891 | code+output | Route-B R–T BEM falsifier chain (v3–v19) + shared gate outputs |
| `GUI/` | 124.1 | 2662 | tooling | VortexRing Lab web app, coil GUIs, Vlab experiment |
| `SST_fs_attachment_audit_research/` | 114.2 | 164 | code+output | Framed-helicity / attachment / Hopfion audits |
| `SST_chi_phase_research/` | 74.9 | 629 | code | Chi-phase Track B (v10B1–v16B0) + chiE Biot–Savart (v0–v7) |
| `SST-dashboard/` | 58.7 | 246 | tooling | PyQt5 SST research dashboard |
| `KnotTheory/` | 45.8 | 614 | vendored | Bar-Natan HFK-Zurich (Python 2) + WikiLink Java |
| `bundles/` | 37.1 | 1 | data | `trefoil_closure.zip` only |
| `SST_horn_bem_research/` | 29.6 | 113 | code | Horn-torus Dirichlet / Neumann BEM packages |
| `SST_Coil_DigitalTwin_research/` | 27.3 | 460 | code | Coil digital twin v1…v10 |
| `SST_timefield_spectral_v06_research/` | 26.9 | 71 | output | Timefield / EPR spectral outputs from contra-swirl v0_6 |
| `SST21D_knot_order_pipeline/` | 19.9 | 886 | code | SST-21D static / Fresnel knot-order table |
| `SST_derive_constants_research/` | 17.8 | 582 | code | Finite-cell / gate derivation manuscripts + scripts |
| `SST_ssdl_audit_research/` | 17.1 | 42 | code | Separatrix surface-density lift audit |
| `generated-figures/` | 13.0 | 391 | output | Robustness / multisector plot archives |
| `templates/` | 10.0 | 24 | tooling | C++ / pybind11 audit template |
| `SST_CoilLab_research/` | 9.8 | 237 | code | Packaged CoilLab v1 / v2_work |
| `SST_v0_8_19_routes_research/` | 7.7 | 199 | code | Planck Routes A–D / Route-A / nonfit / torsion packs |
| `SST_Route_I_relative_entropy_PoC/` | 6.9 | 50 | code | Route-I PoC (only v0.0.4 extracted; rest zip-only) |
| `SST_ideal_trefoil_biot_research/` | 2.7 | 31 | code | Ideal-trefoil Biot–Savart packages |
| `SST_contra_swirl_bridge_research/` | 2.6 | 37 | code | Contra-swirl bridge falsifiers v0…v0_6 |
| `SST_minimal_falsification_harness/` | 1.3 | 57 | code | Minimal α⁻¹ falsification harness |
| `SST_dark_knot_rayleigh_research/` | 1.0 | 33 | code | Dark-knot Rayleigh / rocking audit |
| `SST_Hopf_Benchmark/` | 0.2 | 40 | code | Hopf-charge / spin-route gate packet |
| `scripts/` | 0.2 | 23 | tooling | Repo reorg / merge helpers + their tests |
| `SST_Sutcliffe_HSS_feasibility_gate/` | 0.1 | 20 | code | Hopf-soliton feasibility gate v0.1.0 |
| `experiments/` | 0.0 | 5 | stub | Relocation READMEs + SYCL probes |
| `to_be_processed/` | 0.0 | 1 | stub | Relocation README only |
| `verification-suites/` | 0.0 | 1 | code | Single embedded-knots pytest |
| `.idea/` | 36.9 | 36 | tooling | IDE settings (local) |
| `.cursor/` | 0.0 | 11 | tooling | Cursor plans |
| `.pytest_cache/` / `__pycache__/` | 0.0 | — | cache | Local caches |

Also present but not in the size table above: root files `sst_gilbert_usability.py`,
`test_sst_gilbert_usability.py`, migration manifests, `requirements-workbench.txt`,
`knots_ideal_favorites.txt`.

## Classification of root folders

### Active research packs

Versioned sandboxes with runnable calculation scripts (see [INVENTORY_PYTHON.md](INVENTORY_PYTHON.md)):

- Fermat / geodesic: `SST_fermat_pybind_research`
- BEM / spectral: `SST_routeB_RT_bem_research`, `SST_horn_bem_research`, `SST_ssdl_audit_research`
- Constants: `SST_derive_constants_research`
- Knot / trefoil: `SST_chi_phase_research`, `SST_Trefoil_Closure`, `SST_ideal_trefoil_biot_research`, `SST21D_knot_order_pipeline`, `SST_Hopf_Benchmark`
- Falsifiers / predictions: `SST_dimensionless_dynamic_predictions`, `SST_contact_billiard_hydrodynamic_falsifier`, `SST_minimal_falsification_harness`, `SST_Sutcliffe_HSS_feasibility_gate`, `SST_dark_knot_rayleigh_research`, `SST_Route_I_relative_entropy_PoC`, `SST_v0_8_19_routes_research`
- Coil: `SST_Coil_DigitalTwin_research`, `SST_CoilLab_research`
- Audits / bridges: `SST_fs_attachment_audit_research`, `SST_contra_swirl_bridge_research`, `SST_timefield_spectral_v06_research` (output-only)

### Data / asset trees

`KnotPlot/`, `media/`, `datasets/`, `3D/`, `generated-figures/`, `bundles/`

### Tooling / UI

`scripts/`, `templates/`, `SST-dashboard/`, `GUI/` (including `vortexring-lab`)

### Vendored third-party

- `KnotTheory/HFK-Zurich` — Dror Bar-Natan Knot Floer Homology (Python 2)
- `KnotTheory/WikiLink` — Java / Mathematica MediaWiki connector

### Relocation stubs

`to_be_processed/`, `experiments/derive_constants/`, `experiments/trefoil/closure/`

## Flags (non-source bulk)

| Location | Size | Note |
|----------|-----:|------|
| `Restore_Archives/` | ~2406 MB / 563 zips | **Central zip store** (theme-nested); see [Restore_Archives/README.md](Restore_Archives/README.md) |
| `.tmp.driveupload/` | 4.4 GB / 9051 files | Hidden Google Drive sync staging; not part of the research tree |
| `SST_contact_billiard_hydrodynamic_falsifier/..._v0.2.0/.venv/` | ~280 MB | Virtualenv living inside a research pack |
| `3D/Python/3d_sliced/*.gcode` | ~60 MB | Slicer output, not Python source |
| `KnotPlot/ridgerunner/out/` | ~3.91 GB | Ridgerunner campaign outputs |
| `KnotPlot/knots/` | ~1.08 GB | Per-candidate KnotPlot / RR build trees |

## Quick “where do I run X?”

| Question | Go here |
|----------|---------|
| Newest Fermat / hole-bundle campaign | `SST_fermat_pybind_research/SST_fermat_pybind_research_v0.6.1/` |
| Route-B BEM production scan | `SST_routeB_RT_bem_research/SST_routeB_RT_bem_research_v18/` |
| Derive-constants gate chain | `SST_derive_constants_research/code/` |
| Chi-phase Track B (GP/NLSE) | `SST_chi_phase_research/sst_chi_phase_package_v16B0/` |
| Horn-torus χ_E / trefoil BS | `SST_chi_phase_research/sstcore_chiE_local_v7/` |
| KnotPlot → ridgerunner pipeline | `KnotPlot/ridgerunner/` |
| SST-21D catalogue table | `SST21D_knot_order_pipeline/..._v0.2.0/` → `py -3 -m sst21d` |
| PyQt dashboard | `SST-dashboard/sst_dashboard_app.py` |
| Code that exists only in zips | [INVENTORY_ARCHIVES.md](INVENTORY_ARCHIVES.md) § “Code only inside archives” |
| Nested / duplicate working dirs | [INVENTORY_DUPLICATES.md](INVENTORY_DUPLICATES.md) |
