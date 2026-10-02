# Vortexring Lab — archief

Oudere builds en ontwikkelgeschiedenis. Geen bestanden verwijderd — alleen verplaatst uit de projectroot.

**Actief in root:** `vortexring-lab-v7.6.25b.html` + `vortexring-lab-v6.1.html`.

**v7.6.0–25a:** zie [`../vortexring-lab-v7.6-release-train/`](../vortexring-lab-v7.6-release-train/).

## v7-monoliths (`v7/`)

| Versie | Bestand | Rol |
|---|---|---|
| v7.2.1 … v7.4.1 | `v7/vortexring-lab-v7.*.html` | Vroege v7-lijn |
| bundel r1 | `v7/vortexring-lab-v7.4-sst-bundle-r1.html` | SST-bundel pre-merge |
| v7.4.2 | `v7/vortexring-lab-v7.4.2.html` | Merge-baseline |
| v7.5 … v7.5.3 | `v7/vortexring-lab-v7_5*.html` | Frames, BEM, stretch gate |
| v7.5.4 / v7.5.5 | `v7/vortexring-lab-v7_5_4.html`, `…_5_5.html` | Stretch-gate complete + edge drawers |
| v7.5.4 experimenten | `v7/vortexring-lab-v7_5_4_*.html` | dual-sidebar, zflow, swirl-clock snapshots |

### v7-tools (`v7-tools/`)

Validators en browser-smoke voor gearchiveerde builds. Vanuit `v7-tools/`:

```bash
cd archive/v7-tools
python validate-v7_5_5.py
python validate-v7.4.2.py
```

### Knopencatalogus

Gearchiveerde HTML laadt catalogi via `../../ideal_knots_data.js` (en fourier/knotplot waar van toepassing) vanuit de projectroot.

## v4–v6 geschiedenis (`v4-history/`)

Volledige HTML-ontwikkeltrail v3–v6. Zie [`v4-history/README.md`](v4-history/README.md).

## Duplicates (`duplicates/vendor-root/`)

Root-kopieën van Three.js/KaTeX die naast de canonieke [`../vendor/`](../vendor/) stonden.
