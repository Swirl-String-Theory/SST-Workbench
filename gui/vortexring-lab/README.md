# Vortexring Lab v6.1

Modulaire superfluïde vortex-filamentsimulator (SST-Workbench).

## Starten

Open in een lokale webserver (ES-modules vereisen HTTP, geen `file://`):

```bash
cd GUI/vortexring-lab
npx --yes serve .
# → http://localhost:3000/vortexring-lab-v6.1.html
```

## Structuur

```
vortexring-lab/
  vortexring-lab-v6.1.html   # UI-shell
  app/
    entry.js                 # laadt vendor + app
    vortexring-lab-app.js    # solver, UI, rendering
    physics-bridge.js        # module ↔ legacy API
    load-deps.js             # CDN fallback
  physics/                   # testbare kern (geen WebGL)
  diagnostics/
  tests/vortexlab-regression.mjs
  vendor/                    # optionele offline Three.js/KaTeX
```

## Tests

```bash
npm test
```

Dekt regressies A–F (stap-debet, ring/Kelvin, topologie, segment-contact, passieve diagnose, CFL).

## Offline

Plaats `three.min.js`, `katex.min.js`, `katex.min.css`, `auto-render.min.js` in `vendor/` (zie `vendor/README.md`).

## Legacy

Monolithische kopie: `../vortexring-lab-v4-version-history/vortexring-lab-v6.1.html` (niet meer bijgewerkt).
