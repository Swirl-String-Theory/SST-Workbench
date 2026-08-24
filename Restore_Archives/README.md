# Restore_Archives

## Samenvatting

`Restore_Archives/` bevat **563** zip-pakketten (~2,4 GB): snapshots van SST-onderzoek
(Fermat, Route-B BEM, chi-phase, coil, falsifiers, Maxwell, Route-I, Planck-routes,
trefoil, ideal-links, enz.), plus VortexRing Lab-releases, KnotPlot/ridgerunner-data en
SST_CANON-patches.
De zips zijn de enige lokale archiefkopieën (git negeert `*.zip`); uitgepakte working
trees blijven in de research packs. Ongeveer tachtig bestanden zitten nog in `Misc/` en
wachten op fijnere indeling.

Central home for **all** Workbench `.zip` archives. Research packs keep only their
extracted working trees; zips live here under theme folders.

`.gitignore` excludes `*.zip`, so these files are local-only (not in git).

## Layout

```
Restore_Archives/
  README.md
  _MANIFEST.csv          # last consolidate run (source → dest, sha256)
  Python/                # loose .py dumps from Downloads (not reorganized yet)
  Fermat/                # optional series subdirs e.g. v0.6.1/
  RouteB_BEM/
  ChiPhase/
  Coil/
  VortexLab/
  DeriveConstants/
  Falsifiers/
  Maxwell/
  Dimensionless/
  ContactBilliard/
  Route_I/
  Routes_v0819/
  IdealLinks/
  KelvinFloquet/
  Trefoil/
  Hopf/
  Horn_SSDL/
  FS_Attachment/
  Bridge/
  KnotPlot/
  SST21D/
  ProofScripts/
  Datasets/
  TripleGear/
  Templates/
  Canon/
  Misc/
```

Counts (2026-08-24 after Downloads + Workbench ingest): **563** zips, **~2406 MB**.

## Per thema (1–3 zinnen)

### `Fermat/` (26 zips, ~44 MB)
Versielijn van de Fermat pybind-onderzoekspakketten (v0.1–v0.6.1) plus campaign-/results-zips.
Bevat radiale Fermat-profielen, knot-scans, geodesic/monodromy en hole-bundle audits.
Live uitgepakte tree: `SST_fermat_pybind_research/…_v0.6.1/`.

### `RouteB_BEM/` (27 zips, ~2 MB)
Route-B R–T BEM falsifier-keten: versiepakketten, multigrid/normalizer-suites, BEMv18-scans en BEMv19 link-parser.
Kleine bron-/patch-zips; zware outputs zitten vooral in de uitgepakte `SST_routeB_RT_bem_research/` tree.

### `ChiPhase/` (34 zips, ~48 MB)
Twee lijnen: vroege chi-phase v1–v6 en Track B GP/NLSE v10B–v16B, plus chiE/Biot–Savart lokale packs.
Bevat ook `__from_repo`-varianten waar Downloads en repo-inhoud verschilden.

### `Coil/` (22 zips, ~25 MB)
Coil DigitalTwin / CoilLab exports, Rodin GUI-bundles (v8–v15), Fourier-checks en Halbach/starshaped geometrie.
Uitgepakte code leeft in `SST_Coil_*_research/` en `GUI/coils/`.

### `VortexLab/` (43 zips, ~107 MB)
VortexRing Lab release-train (v4, v7.5.x, v7.6.x), modular M1-extract en sessie-/benchmark-results.
Browser-simulator snapshots; actieve HTML staat onder `GUI/vortexring-lab/`.

### `DeriveConstants/` (29 zips, ~69 MB)
Finite-cell / gate-packages: Derive_Constants manuscripts+code, pressure/GP/phase-budget gates en batch-runs.
Ook Independent FiniteCore SpectralSelector-versies (v0.1.x).
Hoort bij `SST_derive_constants_research/code/` en `Independent_FiniteCore_SpectralSelector/`.

### `Falsifiers/` (16 zips, ~3 MB)
Minimale α⁻¹-falsification harness (v0.1–v0.3 Gilbert/calibration), dark-knot Rayleigh,
counterpulley-α en preferred-frame binary falsifiers.
Kleine bronzips; Sutcliffe zit hier of onder Falsifiers-gerelateerde packs.

### `Dimensionless/` (10 zips, ~29 MB)
Dimensionless dynamic predictions v0.1–v0.4 (background vortex, axial bundle, C9 iso-Γ/A clock) plus outputs.
Inclusief `sst_relclock_checks`; campagnes en Windows batch-wrappers.

### `ContactBilliard/` (2 zips, ~6 MB)
Contact-billiard hydrodynamic falsifier v0.1.0 en v0.2.0 (H0–H8 gates, research matrix).
Uitgepakt onder `SST_contact_billiard_hydrodynamic_falsifier/`.

### `Route_I/` (12 zips, ~6 MB)
Relative-entropy PoC-lijn v0.0.2–v0.1.0 plus Route-I heat-guard patch bundles.
Alleen v0.0.4 is uitgepakt; nieuwste scripts (o.a. v0.1.0 resolved-knot action) zitten nog in de zip.

### `Routes_v0819/` (11 zips, ~6 MB)
Planck Routes A–D evidence/equivalence/v3-preregistered packs, Route-A falsification, nonfit harness en torsion-impedance pybind.
Gedeeld met `SST_v0_8_19_routes_research/`.

### `IdealLinks/` (21 zips, ~45 MB)
Comprehensive ideal-links test suite (v0.1–v0.4-alpha) plus continuum-ladder runners en CMD/reporting patches.
Spiegel van `SST_ideal_links/`; oudere packs uit Misc zijn hierheen verplaatst.

### `KelvinFloquet/` (2 zips, ~0.3 MB)
Kelvin–Floquet Workbench cpp/pybind packages v0.1.0–v0.1.1.
Nieuwe thema-map voor Floquet/Kelvin research-archives.

### `Trefoil/` (14 zips, ~96 MB)
Ideal-trefoil Biot–Savart packages, robustness sweep outputs, trefoil_closure-bundle en gerelateerde patches.
Grote resultaat-archieven naast `SST_Trefoil_Closure/` / `SST_ideal_trefoil_biot_research/`.

### `Hopf/` (7 zips, ~0.6 MB)
Hopf-benchmark packet v0.1 plus SST_Hopf cpp/pybind-lijn v0.1.0–v0.1.4.
Spiegel van `SST_Hopf_Benchmark/`.

### `Horn_SSDL/` (3 zips, ~0.1 MB)
Horn-torus Dirichlet-packages en SSDL-audit v0.2 (separatrix surface-density lift).
Compacte bron-snapshots voor `SST_horn_bem_research/` / `SST_ssdl_audit_research/`.

### `FS_Attachment/` (10 zips, ~25 MB)
Fractional-filament-sea / attachment-audit packages (ffs_00–03) en helicity-resultaten.
Hoort bij `SST_fs_attachment_audit_research/` en dashboard FFS-scripts.

### `Bridge/` (6 zips, ~7 MB)
Contra-swirl bridge resultaten (v0.3–v0.6 timefield) plus CASTLE/Eckvahl Science 2023 EPR-data.
Voedt `SST_contra_swirl_bridge_research/` en `SST_timefield_spectral_v06_research/`.

### `KnotPlot/` (17 zips, ~310 MB)
Grootste datamap: KnotPlot/ridgerunner-bundles, fseries/Fresnel-archieven, ideal_3_1-runs en tooling.
Bron voor `KnotPlot/` working trees en Route-B knot-data.

### `SST21D/` (3 zips, ~2 MB)
SST-21D knot-order pipeline v0.1.0 / v0.2.0 (Gilbert + Fresnel static tables).
Uitgepakt onder `SST21D_knot_order_pipeline/`.

### `ProofScripts/` (3 zips, ~1 MB)
VAM Python benchmarks, knots-for-particles en canon_evidence-snapshots.
Aanvulling op `proof-scripts/swirl/`.

### `Datasets/` (8 zips, ~2 MB)
Paper-/portfolio-zips, SPARC, visualisatie-apps en hydrodynamische H-ground-state artikelen.
Losse datasets naast `datasets/`.

### `TripleGear/` (6 zips, ~59 MB)
3D triple-gear printkits (Printables), Blender-package en parametrische recovery fase 1.
Hoort bij `3D/Triple_Gear/`.

### `Templates/` (1 zip, ~2 MB)
C++/pybind11 audit-template (`SST_cpp_pybind_audit_template`).
Starter voor native research extensions.

### `Canon/` (19 zips, ~114 MB)
SST_CANON release-/patch-bundles (v0.8.x), NotebookLM slide packs, prompt/system zips en Whisper ASR-patches.
Canon-materiaal dat naast SwirlStringTheory-papers werd bewaard.

### `Misc/` (66 zips, ~394 MB)
Restcategorie: losse outputs (`batch_runs`, campaign timestamps), images en nog niet scherp geclassificeerde bundles.
Ideal-links packs zijn naar `IdealLinks/` verplaatst; kandidaat voor verdere herverdeling.

### `Python/` (geen zips)
Losse `.py`-dumps uit Downloads; nog niet per thema gesorteerd.

## How archives were collected


1. Downloads dump was placed in `Sources_Zips/` (now emptied and removed).
2. [`scripts/consolidate_archives.py`](../scripts/consolidate_archives.py) moved those
   zips into theme folders, then moved every remaining Workbench `*.zip` here.
   Later runs also sort zips left in the `Restore_Archives/` root and reclassify
   matching files out of `Misc/` (e.g. IdealLinks).
3. **Collision rule**
   - Same basename + same size + same SHA256 → delete the duplicate (keep one).
   - Same basename, different content → keep both; repo copy named
     `<stem>__from_repo.zip`.

Re-run (dry-run then apply):

```powershell
python scripts/consolidate_archives.py
python scripts/consolidate_archives.py --apply
```

## Finding a pack

| Looking for | Theme folder |
|-------------|--------------|
| Fermat / hole-bundle campaigns | `Fermat/` |
| Route-B BEM | `RouteB_BEM/` |
| Chi-phase / chiE | `ChiPhase/` |
| Coil DigitalTwin / CoilLab / rodin GUIs | `Coil/` |
| VortexRing Lab release train | `VortexLab/` |
| Derive_Constants / FiniteCore SpectralSelector | `DeriveConstants/` |
| Minimal / Sutcliffe / dark-knot / counterpulley / blind falsifier packs | `Falsifiers/` |
| Maxwell SST falsifier chain (v0.1–v0.3) | `Maxwell/` |
| Ideal-links comprehensive test suite | `IdealLinks/` |
| Kelvin–Floquet / Kelvin–Joule / Kelvin–Kirchhoff workbench | `KelvinFloquet/` |
| Route-I relative entropy (incl. unextracted v0.1.0) | `Route_I/` |
| KnotPlot / ridgerunner / fseries data | `KnotPlot/` |
| SST_CANON / NotebookLM patches | `Canon/` |

Extracted working trees stay at the Workbench root (e.g.
`SST_fermat_pybind_research/SST_fermat_pybind_research_v0.6.1/`).

See also [INVENTORY_ARCHIVES.md](../INVENTORY_ARCHIVES.md).
