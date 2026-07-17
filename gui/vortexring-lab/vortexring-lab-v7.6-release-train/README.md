# VortexRing Lab v7.6 release train

## Aanbevolen versie

Open `latest/vortexring-lab-v7.6.10.html`. Houd `ideal_knots_data.js` en `fourier_knots_data.js` in dezelfde map.

## Inhoud

- `releases/`: alle cumulatieve snapshots v7.6.0–v7.6.10.
- `diffs/`: unified diffs tussen opeenvolgende releases.
- `latest/`: de actuele geconsolideerde release.
- `sources/`: oorspronkelijke Gilbert- en `.fseries`-bronnen plus gegenereerde JavaScriptcatalogi.
- `docs/`: swirl-clock- en afstandssweepprotocollen.
- `CHANGELOG.md`: volledige releasegeschiedenis.
- `MIGRATION_FROM_7_5_4.md`: mapping van oude conflicterende bestandsnamen.
- `SHA256SUMS.txt`: integriteitscontrole.

## Status

De speculative swirl-clock blijft duidelijk **Research Track / niet canon / zonder solverkoppeling**.

## Belangrijke hotfixes

`v7.6.7` bevatte een JavaScript bootstrapregressie (zwart canvas met alleen HUD); dit is sinds `v7.6.8` hersteld. `v7.6.9` corrigeert de te sterke falsificatieclaim en de flikkerende quick-overlay. `v7.6.10` herstelt de ontbrekende quick-controlbindings, vrije afstandsinvoer en correcte periodieke-z-behandeling voor verre kalibraties.
