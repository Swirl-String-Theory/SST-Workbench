# Vortexring Lab

Modulaire superfluïde vortex-filamentsimulator (SST-Workbench).

## Actieve entry points

| Build | Bestand | Rol |
|---|---|---|
| **v7.5.5** (primair) | `vortexring-lab-v7_5_5.html` | Border edge-drawers + MODEL-tabbladen (FLOW/VORTEX/KERN/CILINDER) |
| **v7.5.4** (baseline) | `vortexring-lab-v7_5_4.html` | Regressie-anker (stretch gate complete-fixes) |
| **v7.4.2** (baseline) | `vortexring-lab-v7.4.2.html` | Oudere regressie-anker (merge v7.4.1 ⊕ bundel r1) |
| **v6.1** (modulair) | `vortexring-lab-v6.1.html` | ES-module shell → `app/`, `physics/` (`npm test`) |

Oudere v7.5-snapshots (v7.5 … v7.5.3) staan in [`archive/v7/`](archive/v7/).

## Starten

ES-modules en lokale assets vereisen HTTP (geen `file://`):

```bash
cd GUI/vortexring-lab
npx --yes serve .
```

**Primair (dagelijks):**

- http://localhost:3000/vortexring-lab-v7_5_5.html

**Secundair:**

- http://localhost:3000/vortexring-lab-v7_5_4.html — regressie-baseline v7.5.4 (`?selftest=1`)
- http://localhost:3000/vortexring-lab-v7.4.2.html — oudere regressie-baseline (`?selftest=1`)
- http://localhost:3000/vortexring-lab-v6.1.html — modulair testspoor

Zelftests (monolith): voeg `?selftest=1` toe aan de URL.

## Waarom v6.1 apart?

v6.1 is **geen oudere “versie 6” die nog moet fuseren** met v7. Het is een parallel **refactor-spoor**:

- **Architectuur:** ES-modules (`app/entry.js` → `physics/*.js`) die Node direct kan importeren voor `npm test` — zonder browser/WebGL.
- **Featureset:** een kleinere, pre-v7.4 snapshot (~3200 regels app). Mist o.a. SST-bundel, BEM, stretch gate, ModelLog, solver/display-frames en zelftests T8–T13.
- **Doel:** unit-testbare physics-kern (writhe, contact, CFL, Kelvin, …). v7.5.5 is de volledige research-simulator.

Terugport van v7-features naar `physics/` zou een aparte grote refactor zijn; voor dagelijks werk gebruik je v7.5.5.

## Structuur

```
vortexring-lab/
├── vortexring-lab-v7_5_5.html     # actieve monolith (v7.5.5)
├── vortexring-lab-v7_5_4.html     # regressie-baseline v7.5.4
├── vortexring-lab-v7.4.2.html     # regressie-baseline
├── vortexring-lab-v6.1.html       # modulaire entry
├── ideal_knots_data.js            # optionele volledige knopencatalogus
├── extract_core.py, regression.cjs
├── validate-v7_5_5.py, validate-v7_5_4.py, validate-v7.4.2.py
├── browser-smoke-v7_5_5.mjs, browser-smoke-v7_5_4.mjs, browser-smoke-v7.4.2.mjs
├── app/                           # modulaire UI + solver (v6.1)
├── physics/                       # testbare kern (geen WebGL)
├── diagnostics/
├── tests/
├── vendor/                        # offline Three.js/KaTeX (optioneel)
├── docs/                          # planning, release notes, patches
└── archive/                       # oudere v7-builds + v4-geschiedenis
```

## Tests

Node-regressie (modulaire kern, v6.1):

```bash
npm test
```

Statische validators (actieve monolith-builds):

```bash
python validate-v7_5_5.py vortexring-lab-v7_5_5.html
python validate-v7_5_4.py vortexring-lab-v7_5_4.html
python validate-v7.4.2.py vortexring-lab-v7.4.2.html
```

Browser-smoke (Puppeteer, optioneel):

```bash
node browser-smoke-v7_5_5.mjs vortexring-lab-v7_5_5.html
node browser-smoke-v7_5_4.mjs vortexring-lab-v7_5_4.html
node browser-smoke-v7.4.2.mjs vortexring-lab-v7.4.2.html
```

## Documentatie

Zie [`docs/README.md`](docs/README.md) voor stappenplannen, release notes en patch-instructies.

## Archief

Oudere v7-monoliths en de volledige v3–v6 ontwikkeltrail staan in [`archive/README.md`](archive/README.md).

## Offline

Plaats `three.min.js`, `katex.min.js`, `katex.min.css`, `auto-render.min.js` in `vendor/` (zie `vendor/README.md`).
