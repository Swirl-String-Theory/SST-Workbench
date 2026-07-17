# v7.6.10 — Vrije afstand en werkelijk gebonden spec-clockbediening

Parent: `v7.6.9`

## Fixed

- Het numerieke veld voor \(\Delta z_{AB,0}\) is niet langer hard begrensd op de cilinderhoogte; de slider blijft afzonderlijk begrensd op \(2H_{\rm cyl}\).
- Live diagnostiek overschrijft geen actief numeriek invoerveld meer tijdens typen.
- De vier spec-clockgetalvelden wijzigen nu werkelijk dezelfde MODEL-toestand.
- Preset, model-pull, naderen, verwijderen, logging en `log.txt`-export hebben nu expliciete eventbindings.
- Een startafstand groter dan de periodieke z-cel schakelt periodieke z-wrapping automatisch uit en blokkeert herinschakeling zolang de afstand niet in de cel past.
- ModelLog-snapshots bevatten nu ook `zA`, `zB`, initiële afstand, offset, beide driftsnelheden, `lockVz` en de periodieke-z-status.

## Regression coverage

- `T0t`: een afstand van 2.5 m blijft behouden bij een cilinderhoogte van 1.0 m en schakelt periodiek z uit.
- `T0u`: live synchronisatie overschrijft een gefocust quick-veld niet.
- `T0v`: alle spec-clockquick-controls zijn werkelijk gebonden.
- `T0w`: afstandsgetalveld en slider hebben afzonderlijke grenzen.
