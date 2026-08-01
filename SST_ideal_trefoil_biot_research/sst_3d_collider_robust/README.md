# SST 3D Collider — Robuste Cilinder

Geïntegreerde superfluïde ring-/knoop-collider: React UI met formule-uitleg (uit `sst_3d_trefoil_simulator.html`), volledige Biot–Savart-fysica (uit `gem_sst_3d_taylor_caps.html`), en ideal-knot bibliotheek (31 knopen uit `ideal_favorites.txt`).

## Starten

Open [`index.html`](index.html) in een browser (lokaal via file:// of via WAMP).

Vereist internet voor CDN: React, Three.js, Tailwind, KaTeX, Babel.

## Bestanden

| Bestand | Rol |
|---------|-----|
| `index.html` | React shell, HUD, controls, formule-uitleg |
| `js/physics.js` | Biot–Savart, RK2, heliciteit, ideal-knot sampling |
| `js/scene3d.js` | Cilinder 1.0 m × Ø2.0 m, tube-meshes, Taylor caps |
| `js/ideal_knots_data.js` | Gegenereerde knot-DB (Brian Gilbert XML) |
| `ideal_favorites.txt` | Bron-XML (31 knopen) |
| `embed_ideal_favorites.py` | Regenereert `js/ideal_knots_data.js` |

```bash
python embed_ideal_favorites.py
```

## Features

- Topologie: ringen (0₁), trefoil (3₁), ideal knot (dropdown)
- Aantal dragers: 1 centraal / 2 frontale botsing
- Effectieve energie E_eff = αC + βL + γH + ∂V met NL uitlegpanels
- |Γ| 0–50×10⁻³ m²/s, CW/CCW per drager A/B
- Δx ±100 mm, mirror-B optie
- Ω −2…+2 rad/s, v_z drift, tijdversnelling 1–60×
- Taylor caps / separatrix, solid vs hollow core
- Lab / meebewegend referentiekader

## Bronnen

- UI/formule: `../sst_3d_trefoil_simulator.html`
- Fysica/scene: `../gem_sst_3d_taylor_caps.html`
- Ideal knots: `../vortexring-botsing-ideal.html`, `../ideal_favorites.txt`
