# v7.6.8 — Runtime bootstrap hotfix

Parent: `v7.6.7`

## Fixed

- Herstelt het zwarte simulatorcanvas waarbij alleen de HUD zichtbaar bleef.
- Oorzaak: `syncSpecClockQuickControls()` raadpleegde de lexicale `const ModelLog` tijdens de eerste `syncUi()`, vóór initialisatie van `ModelLog` (JavaScript temporal dead zone).
- Vroege loggingchecks gebruiken nu veilig `window.ModelLog`.
- `ModelLog` wordt na initialisatie expliciet op `window` gepubliceerd.
- Vroege bootstrapfouten worden voortaan zichtbaar in de meldingsbalk in plaats van als stil zwart canvas.
- Een ontbrekende THREE.js/CDN-dependency geeft nu een expliciete foutmelding.

## Status

`v7.6.7` is functioneel superseded vanwege deze startupregressie. Gebruik `v7.6.8`.
