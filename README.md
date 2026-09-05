# SST-Workbench

**Research sandbox for Swirl–String Theory**

> This is where hypotheses go to get bruised.

Exploratory proofs, versioned falsifiers, KnotPlot→Ridgerunner geometry intake, GUIs, dashboards, notebooks, figures, datasets, and experimental workflows supporting

- [SSTcore](https://github.com/Swirl-String-Theory/SSTcore) — `pip install SSTcore` · `npm install sst-core` (Node.js)
- [Swirl-String-Theory](https://github.com/Swirl-String-Theory/Swirl-String-Theory) — papers + **SST-CANON**

This repository is **not** the canonical source for SST definitions.  
Canon definitions live in Swirl-String-Theory; stable APIs live in SSTcore; **this** is where campaigns, gates, and geometry pipelines get versioned until they either graduate or fail honestly.

Canon chat: [Gemini notebook — Canon v0.8.36](https://notebook.google.com/notebook/7264029f-6bef-4720-be02-a0ad7b8cddb4)

---

## Three-repo map

| Repository | Role |
|------------|------|
| [Swirl-String-Theory](https://github.com/Swirl-String-Theory/Swirl-String-Theory) | Canonical theory — `papers/`, `SST-CANON/` |
| [SSTcore](https://github.com/Swirl-String-Theory/SSTcore) | Stable C++/Python/Node API — `pip install SSTcore`, `npm install sst-core` |
| **SST-Workbench** (this repo) | Research sandboxes, falsifiers, KnotPlot intake, dashboards, archives |

---

## Layout (catalog domains)

The tree was restructured into **ten top-level domains**. Families carry stable catalog IDs (`A011`, `B001`, `C001`, …); version directories use short names like `A011-v0.3.1`. Legacy flat roots (`SST_Maxwell/`, `KnotPlot/`, …) are gone from the working tree — use catalog paths or `07_scripts/sst_workbench_paths`.

| Domain | Role |
|--------|------|
| `01_research/` | Falsifiers, closures, dynamics, benchmarks, pipelines, exploratory packs |
| `02_libraries/` | Shared libraries (knot geometry, finite-core, numerics) |
| `03_data/` | Knot datasets, external data, media, generated outputs |
| `04_tools/` | KnotPlot/Ridgerunner tools, crawlers, proof scripts, fabrication |
| `05_apps/` | Dashboard, coil GUI, VortexRing Lab, math lab |
| `06_templates/` | Pack / audit templates |
| `07_scripts/` | Repo helpers, path resolver, migration tooling, tests |
| `08_third_party/` | Vendored third-party (e.g. KnotTheory) |
| `09_archive/` | Restore zips and legacy working-tree archives |
| `10_docs/` | Inventory, migration provenance, registry, architecture |

Marker file: `.sst-workbench-root`. Machine catalog index: [`10_docs/registry/catalog_index.json`](10_docs/registry/catalog_index.json). Move provenance: [`10_docs/migration/path_map.csv`](10_docs/migration/path_map.csv).

**Paths:** prefer `import sst_workbench_paths` / `07_scripts/paths.cmd`. Optional legacy junctions can be rebuilt with `07_scripts/bootstrap_junctions.cmd` — do **not** run that casually on a clean tree.

---

## How this maps to Canon v0.8.36

The Canon is stratified: **[ORTHODOX]** / **[DERIVED]** / **[SPECULATIVE]**. Workbench packs are mostly *tests and bridges*, not automatic promotions into the Canon.

| Theme | Catalog home (examples) | Canon touchpoint |
|-------|-------------------------|------------------|
| Maxwell stack | `01_research/A_falsifiers/A011`…`A015` | v0.8.36 Maxwell-stack; do **not** conflate material swirl-tonic velocity with \(\mathbf{A}_{\mathrm{eff}}\) |
| Einstein emergent metric | `A017_einstein_emergent_metric_poisson` | analogue-metric / clock-field bridges |
| Helmholtz vortex gates | `A016_helmholtz_vortex_transport` | vortex-gate falsifiers |
| Kelvin / Floquet | `A019`, `A032`, `A008_chiral_kelvin_core`, `C006_kelvin_floquet_workbench` | Kelvin-mode / Floquet workbenches |
| Finite-core spectral | `02_libraries/B_finite_core/B001_…` | spectroscopic-response guards |
| Geometry provenance | `04_tools/A_geometry` + `03_data/A_knots/04_knotplot` | Canon `PROJ2026-KNOTPLOT-RR-001` → SSTcore `PipelineProvenanceAPI` |

**Interpretation boundary:** geometry proxies and campaign PASS/WARN/SKIP reports are **not** derived physics by themselves. A green gate means the *test* passed under its stated assumptions — not that the Standard Model owes you an apology.

> *delay selects modes, topology protects them.*

---

## Quick start

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install SSTcore
python -m pip install -r requirements-workbench.txt
```

```bash
# Linux / macOS
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install SSTcore
python -m pip install -r requirements-workbench.txt
```

Run commands from the repository root. SSTcore ships as **both** a Python package (`pip install SSTcore`) and a Node.js package (`npm install sst-core`). Most Workbench packs are Python-first; use the npm package for Node / TypeScript (see SSTcore `examples/example_*.ts`).

---

## What lives where (themed map)

Not every version folder is listed. Full inventories: [`10_docs/inventory/root_docs/INVENTORY.md`](10_docs/inventory/root_docs/INVENTORY.md).

### Falsifiers & prediction gates — `01_research/A_falsifiers/`

| Catalog ID | Theme |
|------------|--------|
| `A011`–`A015` | Maxwell kinetic / dynamical / physical-lines / field-null / reciprocal |
| `A017` | Einstein emergent metric / Poisson |
| `A016` | Helmholtz vortex transport |
| `A008`, `A019`, `A032` | Chiral Kelvin / Kirchhoff / Joule transient |
| `A007` | Ideal-links topology robustness |
| `A010` | Counterpulley \(\alpha\) |
| `A009` | Preferred-frame binary |
| `A006` | Contact-billiard hydrodynamic |
| `A005` / harness families | Minimal falsification harness lineage |
| `A004` | Dimensionless dynamic predictions |
| `A003` | Dark-knot Rayleigh |
| `A001`–`A002` | Route-A / Planck-routes packs |

Each family has `FAMILY.yaml` and version dirs `A0xx-v…`. Blind/unblind artifacts stay separate — treat unblind keys carefully.

### Geometry & data — `03_data/` + `04_tools/`

| Path | Role |
|------|------|
| `04_tools/A_geometry/A001_knotplot` | KnotPlot tool surface |
| `04_tools/A_geometry/A002_ridgerunner` | Ridgerunner pipeline |
| `03_data/A_knots/04_knotplot` | Shared `final` knot dataset |
| `03_data/A_knots/01_ideal/ideal_sources` | Ideal knot/link archives + provenance |
| `03_data/A_knots/02_fourier/…` | Fremlin / KnotPlot Fourier series |
| `03_data/A_knots/03_katlas/v0.2.2` | Katlas sources |
| `03_data/A_knots/07_knotinfo` | KnotInfo upstream archives |
| `08_third_party/knot_theory` | Vendored Bar-Natan HFK-Zurich + WikiLink |

Resolver helpers: `sst_workbench_paths.knot_dataset()`, `.ideal_sources()`, `.katlas_sources()`, `.fseries_root()`.

### Labs & apps — `05_apps/`

| Path | Role |
|------|------|
| `A001_dashboard/` | PyQt research dashboard (`sst_dashboard_app.py`) |
| `A002_coil_gui/` | Coil GUI |
| `A003_vortexlab/vortexring-lab/` | VortexRing Lab (HTML/JS) |
| `A004_math_lab/` | Math lab packs |

### Other research domains

| Domain letter | Path prefix | Examples |
|---------------|-------------|----------|
| Closures | `01_research/B_closures/` | derive-constants, Route-B BEM, horn/SSDL, contra-swirl |
| Dynamics | `01_research/C_dynamics/` | chi-phase, ideal-trefoil Biot, Kelvin Floquet workbench |
| Benchmarks | `01_research/D_benchmarks/` | Hopf, verification suites, KnotPlot atlases |
| Pipelines | `01_research/E_pipelines/` | KnotPlot campaigns, PTSA, Katlas conditioning |
| Exploratory | `01_research/F_exploratory/` | coil digital twin / coil lab, Route-I PoC |

### Proofs, archives, docs

| Path | Role |
|------|------|
| `04_tools/D_proof/D001_proof_scripts/` | SSTcore probes + proof trees |
| `03_data/B_external/`, `C_media/`, `D_generated/` | Datasets, media, generated figures/outputs |
| `09_archive/restore/` | Central local zip store (themed) |
| `10_docs/` | Inventory, migration, registry, architecture |
| `06_templates/` | C++/pybind audit and pack templates |
| `07_scripts/` | Resolvers, gates, consolidate/migration scripts, pytest |

Root keepers: `README.md`, `falsifier_registry.yaml`, `requirements-workbench.txt`, `pyrightconfig.json`.

---

## Common entry points

| What | Path | Command |
|------|------|---------|
| SST dashboard | `05_apps/A001_dashboard/sst_dashboard_app.py` | `python 05_apps/A001_dashboard/sst_dashboard_app.py` |
| Full probe harness | `04_tools/D_proof/D001_proof_scripts/` | see pack README; typically `python …/SSTcore_full_probe.py` |
| Embedded-knots tests | `01_research/D_benchmarks/D003_verification_suites/` | `pytest 01_research/D_benchmarks/D003_verification_suites` |
| Gilbert usability | `07_scripts/` | `python -m pytest 07_scripts/test_sst_gilbert_usability.py` |
| Repo tooling tests | `07_scripts/` | `python -m pytest 07_scripts` |
| Maxwell / other falsifiers | `01_research/A_falsifiers/A0xx_…/A0xx-v…/` | Prefer latest version dir; respect blind/unblind |

---

## Docs in this repo

| Doc | Contents |
|-----|----------|
| [INVENTORY.md](10_docs/inventory/root_docs/INVENTORY.md) | Measured overview |
| [INVENTORY_PYTHON.md](10_docs/inventory/root_docs/INVENTORY_PYTHON.md) | Research scripts by pack |
| [INVENTORY_ARCHIVES.md](10_docs/inventory/root_docs/INVENTORY_ARCHIVES.md) | Zip ↔ folder bundles |
| [INVENTORY_FALSIFIERS.md](10_docs/inventory/root_docs/INVENTORY_FALSIFIERS.md) | Falsifier inventory |
| [family_hierarchy.json](10_docs/registry/family_hierarchy.json) | Live hierarchy: families → versions → outputs (+ naming rules) |
| [catalog_index.json](10_docs/registry/catalog_index.json) | Compact catalog index for `resolve_family()` |
| [path_map.csv](10_docs/migration/path_map.csv) | Old → new path provenance |
| [WORKBENCH_LAYOUT.md](10_docs/migration/WORKBENCH_LAYOUT.md) | Historical layout notes |
| [MIGRATION_MANIFEST.md](10_docs/migration/MIGRATION_MANIFEST.md) | Earlier move log |
| [sp11_decommission.md](10_docs/migration/sp11_decommission.md) | Junction teardown / soft-retire |
| [delete_retirement.md](10_docs/migration/delete_retirement.md) | Why `DELETE/` was emptied and removed |
| [09_archive/restore/README.md](09_archive/restore/README.md) | Archive theme layout |
| [.cursor/plans/restructure/](.cursor/plans/restructure/) | Restructure epic + SP00–SP11 plans |

---

## Not in git (usually)

| Excluded | Reason |
|----------|--------|
| `09_archive/restore/` zip contents, many `*.zip` | Snapshot store; see archive README |
| Heavy fabrication / slicer output under `04_tools/C_fabrication/` | STL / gcode assets |
| `*.pyd` | Compiled extensions — install SSTcore via pip |
| `*.blend` | Blender scenes |
| `.idea/`, `.venv/` | IDE / local env |

This sandbox may contain **more version folders than particles**. That is not a bug; it is a laboratory.

---

## Provenance (short)

SST’s written history and early theory drafts:

- [2013 Hypotheses on Constants in Quantum Mechanics, using Classical Logic](https://docs.google.com/document/d/1YjhB4Z01CNf3p-W_sCDBcsK4tHlXZnmRRS5NOFviIH8/edit?usp=sharing) (first canon attempt)
- [Fundamental considerations for the theory of the liquid æther](https://docs.google.com/document/d/1PZpK9MFv8t3XsWils4dxlhmRndhp5tNygtDXByGUdH0/edit?usp=sharing)
- Notebooks PDF: see [org README — Origin](https://github.com/Swirl-String-Theory/Swirl-String-Theory#origin-2012--now)

---

## Author

**Omar Iskandarani**  
Independent Researcher, Groningen, The Netherlands  
ORCID: [0009-0006-1686-3961](https://orcid.org/0009-0006-1686-3961)  
Email: `info@omariskandarani.com`

Conceived, written, and (sometimes reluctantly) sandboxed.

---

## Warning

This repository may induce:

- spontaneous fluid metaphors,
- academic eye-rolling,
- an unhealthy attachment to version folders named `A011-v0.1.2.4`,
- the belief that every trefoil deserves its own falsifier.

Proceed responsibly. Geometry is not physics until the Canon says so — and even then, check the epistemic tag.

---

## Feedback

- Open an [issue](https://github.com/Swirl-String-Theory/SST-Workbench/issues)
- Prefer contributing mature closures **up** into SSTcore / Canon rather than forking yet another nested copy
- Or send critiques into the æther. It’s always listening.

---

## License

There is **no single root LICENSE** in this sandbox. Nested packs may carry their own notices.

Sibling programme defaults: **[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)**  
© 2012–2026 Omar Iskandarani.

Educational and research use welcome. Commercial reuse requires permission.
