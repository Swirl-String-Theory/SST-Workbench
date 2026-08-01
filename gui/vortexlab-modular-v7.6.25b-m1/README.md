# VortexLab modularisatie M1

Bron: `vortexring-lab-v7.6.25b.html`  
Wetenschappelijke versie: **7.6.25b**  
Architectuurmijlpaal: **M1 — parity-safe extraction**

## Wat is gewijzigd

- HTML staat in `apps/web/index.html`.
- CSS staat bytegetrouw in `apps/web/styles/vortexlab.css`.
- De bestaande browserruntime staat bytegetrouw in `apps/web/src/legacy/vortexlab-runtime.js`.
- Three.js en KaTeX worden lokaal uit `apps/web/vendor` geladen.
- Ideal-, Fseries- en KnotPlot-catalogi staan in `apps/web/data`.
- Er is een eerste contractpackage en een proces-geïsoleerde SSTcore-adapterskeleton toegevoegd.

## Wat is nadrukkelijk niet gewijzigd

Geen enkele formule, solverfunctie, gate, catalogusentry of UI-eventhandler is herschreven. M1 verandert alleen bestandsgrenzen en laadpaden.

## Starten

```bash
npm start
```

Open daarna `http://127.0.0.1:4173`.

## Pariteit controleren

```bash
npm run check
```

De verificatie controleert de SHA-256 van de geëxtraheerde runtime, CSS, catalogi en lokale vendorbestanden.

## Volgende mijlpaal

M2 splitst `src/legacy/vortexlab-runtime.js` per domein met expliciete dependencies, maar alleen nadat de browserbenchmarks van M1 dezelfde resultaten geven als v7.6.25b.
