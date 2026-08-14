# 🧪 SST-Workbench

**Research sandbox for Swirl–String Theory**

> This is where hypotheses go to get bruised.

Exploratory proofs, versioned falsifiers, KnotPlot→Ridgerunner geometry intake, GUIs, dashboards, notebooks, figures, datasets, and experimental workflows supporting

- [SSTcore](https://github.com/Swirl-String-Theory/SSTcore) — `pip install SSTcore` · `npm install sst-core` (Node.js)
- [Swirl-String-Theory](https://github.com/Swirl-String-Theory/Swirl-String-Theory) — papers + **SST-CANON**

This repository is **not** the canonical source for SST definitions.  
Canon definitions live in Swirl-String-Theory; stable APIs live in SSTcore; **this** is where campaigns, gates, and geometry pipelines get versioned until they either graduate or fail honestly.

Canon chat: [Gemini notebook — Canon v0.8.36](https://notebook.google.com/notebook/7264029f-6bef-4720-be02-a0ad7b8cddb4)

---

## 🧭 Three-repo map

| Repository | Role |
|------------|------|
| [Swirl-String-Theory](https://github.com/Swirl-String-Theory/Swirl-String-Theory) | Canonical theory — `papers/`, `SST-CANON/` |
| [SSTcore](https://github.com/Swirl-String-Theory/SSTcore) | Stable C++/Python/Node API — `pip install SSTcore`, `npm install sst-core` |
| **SST-Workbench** (this repo) | Research sandboxes, falsifiers, KnotPlot intake, dashboards, archives |

---

## 📐 How this maps to Canon v0.8.36

The Canon is stratified: **[ORTHODOX]** / **[DERIVED]** / **[SPECULATIVE]**. Workbench packs are mostly *tests and bridges*, not automatic promotions into the Canon.

| Theme | Typical packs | Canon touchpoint |
|-------|---------------|------------------|
| Maxwell swirl-tonic / kinetic / reciprocal / mechanical | `SST_Maxwell/` (1–5, **v0.2.0**) | v0.8.36 Maxwell-stack; do **not** conflate material swirl-tonic velocity with \(\mathbf{A}_{\mathrm{eff}}\) |
| Einstein emergent metric / Poisson | `SST_Einstein/` (**v0.1.0**) | analogue-metric / clock-field bridges |
| Helmholtz vortex gates | `SST_Helmholtz/` (**v0.1.0**) | vortex-gate falsifiers |
| Kelvin / Floquet | `SST_Kelvin_Floquet/` (**v0.1.1**), `SST_Chiral-Kelvin-Mode/` | Kelvin-mode suppression / Floquet workbenches |
| Spectroscopic / finite-core | `Independent_FiniteCore_SpectralSelector/` | spectroscopic-response guards |
| Geometry provenance | `KnotPlot/` → ridgerunner → `knots/final` | Canon `PROJ2026-KNOTPLOT-RR-001` → SSTcore `PipelineProvenanceAPI` |

**Interpretation boundary:** geometry proxies and campaign PASS/WARN/SKIP reports are **not** derived physics by themselves. A green gate means the *test* passed under its stated assumptions — not that the Standard Model owes you an apology.

Slogan from the Canon, which this sandbox tries to honour:

> *delay selects modes, topology protects them.*

---

## 🚀 Quick start

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

Run commands from the repository root. SSTcore ships as **both** a Python package (`pip install SSTcore`) and a Node.js package (`npm install sst-core`) — not as a sibling path / submodule. Most Workbench packs are Python-first; use the npm package when you are in Node / TypeScript (see SSTcore `examples/example_*.ts`).

---

## 🗺 What lives here (themed map)

This tree is large on purpose. Below is a **themed** map, not a dump of every nested version folder. For measured sizes and duplicates see [INVENTORY.md](INVENTORY.md).

### Falsifiers & prediction gates

| Path | Latest (approx.) | Notes |
|------|------------------|-------|
| `SST_Maxwell/` | **v0.2.0** (packs 1–5) | Kinetic, dynamical-field, physical-lines, mechanical, reciprocal; target-blind keys exist — treat unblind folders with care |
| `SST_Einstein/` | **v0.1.0** | Blind falsifier + emergent-metric / Poisson closure gates |
| `SST_Helmholtz/` | **v0.1.0** | Helmholtz vortex-gates falsifier |
| `SST_Kelvin_Floquet/` | **v0.1.1** | C++/pybind Kelvin-wave / Floquet workbench |
| `SST_Chiral-Kelvin-Mode/` | **v0.1.3.x** | Chiral Kelvin falsification lineage |
| `SST_Hopf_Benchmark/` | **v0.1.4** | Hopf H0–H10 C++/pybind benchmark |
| `SST_ideal_links/` | **v0.3.6.1** (+ `v0.4.0-alpha.1`) | Ideal-links comprehensive suite |
| `SST_counterpulley_alpha_falsifier/` | **v0.5.0** | Counterpulley \(\alpha\) falsifier |
| `SST_preferred_frame_binary_falsifier/` | **v0.1.1** | Preferred-frame binary falsifier |
| `SST_contact_billiard_hydrodynamic_falsifier/` | **v0.2.0** | Contact-billiard hydrodynamic falsifier |
| `SST_minimal_falsification_harness/` | **v0.3.0** | Minimal \(\alpha^{-1}\) harness |
| `SST_dimensionless_dynamic_predictions/` | **v0.4.0** | Dimensionless knot dynamics / iso-Γ predictions |
| `Independent_FiniteCore_SpectralSelector/` | **v0.1.2.4** | Finite-core spectral selector |
| `SST_Sutcliffe_HSS_feasibility_gate/` | **v0.1.0** | Hopf-soliton feasibility gate |
| `SST_dark_knot_rayleigh_research/` | — | Dark-knot Rayleigh / rocking audits |

### Geometry intake (Canon provenance)

| Path | Role |
|------|------|
| `KnotPlot/` | SST geometry intake — presets, ridgerunner pipeline, `knots/final` shared with falsifiers. **Not** a physics solver. |
| `Ideal_Sources/` | Ideal knot/link geometry archives + provenance |
| `KnotTheory/` | Vendored Bar-Natan HFK-Zurich (Python 2) + WikiLink |

Downstream of certified geometry: **SSTcore** resource APIs and `PipelineProvenanceAPI`.

### Labs & dashboards

| Path | Role |
|------|------|
| `GUI/vortexring-lab/` | VortexRing Lab (HTML/JS monolith + modular tracks) |
| `SST-dashboard/` | PyQt research dashboard |
| `SST_CoilLab_research/` / `SST_Coil_DigitalTwin_research/` | Coil lab / digital twin packs |
| `3D/` | Coil / gear / mold STL generators and slicer outputs |

### Research packs (calculation sandboxes)

| Theme | Paths |
|-------|-------|
| Fermat / geodesic | `SST_fermat_pybind_research/` (live ~v0.6.1) |
| Route-B BEM | `SST_routeB_RT_bem_research/` (v18 production scan lineage) |
| Horn / SSDL | `SST_horn_bem_research/`, `SST_ssdl_audit_research/` |
| Constants | `SST_derive_constants_research/` |
| Chi-phase / Biot | `SST_chi_phase_research/` (not under `to_be_processed/` — that is a stub) |
| Trefoil | `SST_Trefoil_Closure/`, `SST_ideal_trefoil_biot_research/` |
| SST-21D | `SST21D_knot_order_pipeline/` |
| Attachment / contra-swirl | `SST_fs_attachment_audit_research/`, `SST_contra_swirl_bridge_research/` |
| Routes / Route-I | `SST_v0_8_19_routes_research/`, `SST_Route_I_relative_entropy_PoC/` |
| Timefield outputs | `SST_timefield_spectral_v06_research/` (often output-only) |

### Proofs, data, media, archives

| Path | Role |
|------|------|
| `proof-scripts/` | SSTcore probes + swirl/VAM proof trees |
| `datasets/` | SPARC, exports, visualizers |
| `generated-figures/` | Plot archives |
| `media/` | Images, presentations, voiceovers |
| `Restore_Archives/` | **Central** local zip store (theme folders) — not the old `archive/` story |
| `bundles/` | Occasional zip bundles (e.g. trefoil) |
| `scripts/`, `templates/` | Repo helpers; C++/pybind audit template |
| `verification-suites/` | Thin (mainly embedded-knots) |
| `experiments/`, `to_be_processed/` | **Relocation stubs** — real content lives at the research roots above |

---

## ▶️ Common entry points

| What | Path | Command |
|------|------|---------|
| SST dashboard | `SST-dashboard/sst_dashboard_app.py` | `python SST-dashboard/sst_dashboard_app.py` |
| Full probe harness | `proof-scripts/SSTcore_full_probe.py` | `python proof-scripts/SSTcore_full_probe.py` |
| Embedded-knots tests | `verification-suites/embedded-knots/` | `pytest verification-suites/embedded-knots/` |
| Gilbert usability | root | `python -m unittest test_sst_gilbert_usability` |
| Derive / BEM packs | `SST_derive_constants_research/`, `SST_routeB_RT_bem_research/`, … | See each pack README / [INVENTORY_PYTHON.md](INVENTORY_PYTHON.md) |
| Chi-phase | `SST_chi_phase_research/` | Each package has its own README |
| Maxwell campaign | `SST_Maxwell/` | Prefer **v0.2.0** trees; respect blind/unblind boundaries |

---

## 📚 Docs in this repo

| Doc | Contents |
|-----|----------|
| [INVENTORY.md](INVENTORY.md) | Measured overview, directory roles, stale-doc corrections |
| [INVENTORY_PYTHON.md](INVENTORY_PYTHON.md) | Research scripts by pack |
| [INVENTORY_ARCHIVES.md](INVENTORY_ARCHIVES.md) | Zip ↔ folder bundles |
| [INVENTORY_DUPLICATES.md](INVENTORY_DUPLICATES.md) | Nested / duplicated trees |
| [WORKBENCH_LAYOUT.md](WORKBENCH_LAYOUT.md) | Directory map / origins (partially superseded by INVENTORY) |
| [Restore_Archives/README.md](Restore_Archives/README.md) | Theme layout + consolidate script |
| [MIGRATION_MANIFEST.md](MIGRATION_MANIFEST.md) | Historical move-only migration log (rev. 5) |

---

## 🚫 Not in git (usually)

Large or generated binaries stay local / ignored:

| Excluded | Reason |
|----------|--------|
| `Restore_Archives/` contents, many `*.zip` | Snapshot store; see Restore_Archives README |
| `hardware/`, heavy `3D/` slicer output | STL / gcode assets |
| `*.pyd` | Compiled SSTcore — install via `pip install SSTcore` |
| `*.blend` | Blender scenes |
| `.idea/`, `.venv/` | IDE / local env |

This sandbox may contain **more version folders than particles**. That is not a bug; it is a laboratory.

---

## 🧬 Provenance (short)

SST’s written history and early theory drafts:

- [2013 Hypotheses on Constants in Quantum Mechanics, using Classical Logic](https://docs.google.com/document/d/1YjhB4Z01CNf3p-W_sCDBcsK4tHlXZnmRRS5NOFviIH8/edit?usp=sharing) (first canon attempt)
- [Fundamental considerations for the theory of the liquid æther](https://docs.google.com/document/d/1PZpK9MFv8t3XsWils4dxlhmRndhp5tNygtDXByGUdH0/edit?usp=sharing)
- Notebooks PDF: see [org README — Origin](https://github.com/Swirl-String-Theory/Swirl-String-Theory#origin-2012--now)

---

## 🔬 Author

**Omar Iskandarani**  
Independent Researcher, Groningen, The Netherlands  
ORCID: [0009-0006-1686-3961](https://orcid.org/0009-0006-1686-3961)  
Email: `info@omariskandarani.com`

Conceived, written, and (sometimes reluctantly) sandboxed.

---

## ⚠️ Warning

This repository may induce:

- spontaneous fluid metaphors,
- academic eye-rolling,
- an unhealthy attachment to version folders named `v0.1.2.4`,
- the belief that every trefoil deserves its own falsifier.

Proceed responsibly. Geometry is not physics until the Canon says so — and even then, check the epistemic tag.

---

## 💬 Feedback

- Open an [issue](https://github.com/Swirl-String-Theory/SST-Workbench/issues)
- Prefer contributing mature closures **up** into SSTcore / Canon rather than forking yet another nested copy
- Or send critiques into the æther. It’s always listening.

---

## License

There is **no single root LICENSE** in this sandbox. Nested packs may carry their own notices.

Sibling programme defaults: **[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)**  
© 2012–2026 Omar Iskandarani.

Educational and research use welcome. Commercial reuse requires permission.
