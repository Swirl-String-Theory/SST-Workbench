# Vortexring Lab

Superfluïde vortex-filamentsimulator (SST-Workbench).

## Actieve entry points

| Build | Bestand | Rol |
|---|---|---|
| **v7.6.25b** (primair) | `vortexring-lab-v7.6.25b.html` | Huidige monolith — KnotPlot-catalogus, reach/DCSD, spec-clock research track |
| **v6.1** (modulair) | `vortexring-lab-v6.1.html` | ES-module shell → `app/`, `physics/` (`npm test`) |

Oudere builds staan in [`vortexring-lab-v7.6-release-train/`](vortexring-lab-v7.6-release-train/) (v7.6.0–25a) en [`archive/`](archive/) (pre-v7.6).

## Starten

ES-modules en lokale assets vereisen HTTP (geen `file://`):

```bash
cd GUI/vortexring-lab
npx --yes serve .
```

- http://localhost:3000/vortexring-lab-v7.6.25b.html — primair
- http://localhost:3000/vortexring-lab-v6.1.html — modulair testspoor

Zelftests (monolith): voeg `?selftest=1` toe aan de URL.

## Waarom v6.1 apart?

v6.1 is een parallel **refactor-spoor** (ES-modules + Node-tests), geen oudere “versie 6” die nog moet fuseren met v7. Voor dagelijks research-werk gebruik je v7.6.25b.

## Structuur

```
vortexring-lab/
├── vortexring-lab-v7.6.25b.html   # actieve monolith
├── vortexring-lab-v6.1.html       # modulaire entry
├── ideal_knots_data.js            # Brian Gilbert ideal/tight catalogus
├── fourier_knots_data.js          # .fseries-curven
├── knotplot_knots_data.js         # KnotPlot uniform-N300 catalogus
├── build_knotplot_knots_data.py
├── extract_core.py, regression.cjs
├── app/  physics/  diagnostics/  tests/  vendor/
├── docs/                          # planning, release notes, patches
├── archive/                       # pre-v7.6 monoliths + tooling
├── validation/                    # benchmark-/validatie-artefacten
└── vortexring-lab-v7.6-release-train/   # v7.6.0–25a geschiedenis
```

## Tests

Node-regressie (modulaire kern, v6.1):

```bash
npm test
```

Gearchiveerde validators: zie `archive/v7-tools/` (draai vanuit die map).

## Offline

Plaats Three.js/KaTeX in `vendor/` (zie `vendor/README.md`). Root-duplicaten staan in `archive/duplicates/vendor-root/`.

## Documentatie & archief

- [`docs/README.md`](docs/README.md) — planning, releases, patches
- [`archive/README.md`](archive/README.md) — pre-v7.6 geschiedenis
- [`vortexring-lab-v7.6-release-train/README.md`](vortexring-lab-v7.6-release-train/README.md) — v7.6 release train
