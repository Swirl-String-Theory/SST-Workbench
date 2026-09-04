# VortexLab v7.6.24f2

UI/workflow-hotfix op basis van v7.6.24f1. Solver, datasets, scenario-inhoud en researchgates zijn niet gewijzigd.

## Testrunners

- De runnerhub gebruikt nu een responsieve flex-layout. Bij een bredere CLOCK-sidebar komen automatisch meer knoppen op dezelfde rij; de knoppen rekken niet langer vast in twee brede kolommen.
- De vereiste ENGINE-volgorde is zichtbaar en wordt afgedwongen:
  1. SPEC CLOCK · 10-run
  2. Proxy-decompositie
  3. Geselecteerde holdouts
  4. Continuüm N=128–768
  5. Volledige confirmatoire suite
- Een volgende stap ontgrendelt uitsluitend na `ENGINE PASS`; een `RESEARCH FAIL` blokkeert de workflow niet.
- Iedere runner gebruikt één knop die tijdens de run verandert van `Start` naar `Stop`.
- De twee oude afzonderlijke stopknoppen zijn verborgen, maar blijven intern als compatibiliteitsbinding bestaan.
- De ontgrendelstatus wordt per browsertab in `sessionStorage` bewaard.
- Een nieuwe SPEC-run maakt downstreamresultaten opnieuw ongeldig. Een gewijzigde knoop-/bronselectie vergrendelt holdouts en continuüm opnieuw.

## Onderste HUD

- LIVE STABILITEIT, SPEC CLOCK, STATS en SPARK kunnen via de volledige titelbalk én een randzone van 9 px worden gesleept.
- Dubbelklik op titel of rand klapt het venster in.
- `Shift` + dubbelklik dockt een venster terug en klapt het vervolgens in.
- Zwevende vensters hebben een zichtbare buitenrand, zodat de dragzone herkenbaar is.
- Positie, breedte en open/dicht-status blijven persistent.

## Validatie

- Inline JavaScript: syntax PASS.
- 447 statische DOM-id's, geen duplicaten.
- Workflowtransities in een Node-runtimeharnas: PASS.
- `velocityCore`, `velAll`, `rk4Step` en `topologyClearance`: byte-identiek aan v7.6.24f1.
- Clean diff en ZIP-integriteit gecontroleerd.
- Headless Chromium hing in de container vóór DOM-export; interactieve drag-/responsive-/WebGL-validatie blijft lokaal nodig.
