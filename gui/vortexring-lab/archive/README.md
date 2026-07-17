# Vortexring Lab — archief

Oudere builds en ontwikkelgeschiedenis. Geen bestanden verwijderd — alleen verplaatst uit de projectroot.

## v7-monoliths (`v7/`)

| Versie | Bestand | Rol |
|---|---|---|
| v7.2.1 | `v7/vortexring-lab-v7.2.1.html` | Exacte afstanden, Wr/Lk/ACN, trefoil-Wr |
| v7.3 | `v7/vortexring-lab-v7.3.html` | Dock, kernstraal, ModelLog |
| v7.3.1 | `v7/vortexring-lab-v7.3.1.html` | Hotfix op v7.3 |
| v7.4 | `v7/vortexring-lab-v7.4.html` | Positionering, GP-Δ, capaciteitsscheiding |
| v7.4.1 | `v7/vortexring-lab-v7.4.1.html` | Auditcorrecties (provenance, pseudo-energie eruit) |
| bundel r1 | `v7/vortexring-lab-v7.4-sst-bundle-r1.html` | SST-vortexbundel research-track (pre-merge) |
| v7.5 | `v7/vortexring-lab-v7_5.html` | Frames ontvlochten (superseded door v7.5.4) |
| v7.5.1 | `v7/vortexring-lab-v7_5_1.html` | Provenance/geo-diagnostiek |
| v7.5.2 | `v7/vortexring-lab-v7_5_2.html` | BEM + topology guard |
| v7.5.3 | `v7/vortexring-lab-v7_5_3_stretch_gate.html` | Stretch gate |

**Actief in root (niet gearchiveerd):** v7.5.4 (primair), v7.4.2 (regressie-baseline).

### v7-tools (`v7-tools/`)

Validators en smoke-tests voor gearchiveerde builds. Draai vanuit `v7-tools/`:

```bash
cd archive/v7-tools
python validate-v7.4.1.py
python validate-v7.4.py
python validate-v7.3.1.py
node browser-smoke-v7.3.1.mjs
```

Root-validators voor oudere v7.5-snapshots (indien nog aanwezig): `validate-v7_5.py`, `validate-v7_5_1.py` in projectroot.

Extract-artefact: `_inline-v7.4.2.js` (geëxtraheerde kern uit v7.4.2-merge).

### Knopencatalogus

Gearchiveerde HTML laadt `ideal_knots_data.js` via `../../ideal_knots_data.js` (root).

## v4–v6 geschiedenis (`v4-history/`)

Volledige HTML-ontwikkeltrail van v3 baseline t/m v6 step-12. Zie [`v4-history/README.md`](v4-history/README.md) voor chronologie, entry points en `MANIFEST_SHA256.txt`.

**v6.1 modulair** (`../vortexring-lab-v6.1.html`) blijft actief in root — parallel refactor-spoor, geen gearchiveerde monolith.

Vroegere locatie `GUI/vortexring-lab-v4-version-history/` verwijst nu hierheen.
