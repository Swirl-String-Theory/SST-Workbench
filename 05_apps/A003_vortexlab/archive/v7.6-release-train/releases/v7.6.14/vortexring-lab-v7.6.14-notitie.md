# VortexLab v7.6.14 — onafhankelijke vierpaneel-layout

## Doel

De vier primaire zijpanelen zijn niet langer per zijde of als links/rechts-paar gekoppeld. `INFO`, `FLOW`, `KERN` en `DIAG` kunnen ieder afzonderlijk worden geopend en gesloten. Hierdoor zijn alle toestanden met nul, één, twee, drie of vier zichtbare panelen mogelijk.

## Paneelvolgorde

De positie wordt dynamisch bepaald door de zichtbare panelen.

- Linkerkant, buiten naar binnen: `INFO → FLOW → canvas`.
- Rechterkant, binnen naar buiten: `canvas → KERN → DIAG`.

Praktisch betekent dit:

- Alleen `FLOW` open: FLOW staat direct naast de linker rail.
- `INFO` daarna openen: INFO verschijnt buiten FLOW en FLOW schuift één paneelbreedte richting het midden.
- Alleen `KERN` open: KERN staat direct naast de rechter rail.
- `DIAG` daarna openen: DIAG verschijnt buiten KERN en KERN schuift één paneelbreedte richting het midden.

De volgorde blijft dus inhoudelijk stabiel zonder lege gereserveerde paneelplaatsen.

## Onafhankelijke bediening

De vroegere automatische koppelingen zijn verwijderd:

- INFO opent DIAG niet meer automatisch.
- DIAG opent INFO niet meer automatisch.
- FLOW opent KERN niet meer automatisch.
- KERN opent FLOW niet meer automatisch.
- Op smallere vensters wordt de andere zijde niet meer automatisch gesloten.

Elke railknop gebruikt nu een eigen `aria-pressed`-status en een eigen persistente open/dicht-instelling in `localStorage`:

- `vortexlab.quad.left.info.open`
- `vortexlab.quad.left.flow.open`
- `vortexlab.quad.right.core.open`
- `vortexlab.quad.right.diag.open`

Standaard opent v7.6.14 met FLOW en KERN zichtbaar; INFO en DIAG blijven gesloten. De gebruiker kan daarna iedere combinatie kiezen.

## RUN in de header

`SCENARIO & RUN` is uit de linker rail verwijderd en staat nu als zelfstandige `RUN ▾`-dropdown in de header, naast `VIEW ▾`.

De header behoudt de directe primaire bediening:

- vortex reset;
- particle reset;
- pauze/hervatten;
- simulatiesnelheid;
- preset;
- kwaliteit;
- medium.

De RUN-dropdown bevat de uitgebreidere scenariofuncties, tijdomkering, logging en benchmarkbediening. RUN en VIEW hebben unieke menu-ID's en sluiten elkaar bij openen automatisch, zodat twee overlappende headerdropdowns niet tegelijk zichtbaar blijven.

## Canvas-overlays

De onderste overlays houden nu rekening met het aantal zichtbare panelen aan beide zijden. De linker én rechter vrije marge worden dynamisch aangepast voor nul, één of twee open panelen per zijde.

## Versie/provenance

- Versie: `7.6.14`
- Parent: `7.6.13`
- Basis: `7.5.3`
- Nieuwe patchtags:
  - `independent-four-panel-docks`
  - `run-header-dropdown`
  - `independent-panel-persistence`
  - `dual-overlay-offsets`

De fysische solver, SPEC CLOCK-benchmark, Biot–Savart/LIA-routes, topology guard en kernmodellen zijn niet gewijzigd.

## Validatie

Uitgevoerd:

- inline JavaScript: `node --check` geslaagd;
- HTML-audit: 399 unieke ID's, geen duplicaten;
- CSS-parser: geen parsefouten;
- statische regressiechecks:
  - oude `vlCreateDock` verwijderd;
  - links/rechts-pairing verwijderd;
  - responsive auto-close verwijderd;
  - RUN niet meer in de zijrail;
  - afzonderlijke RUN- en VIEW-dropdowns aanwezig;
  - vaste slotvolgorde `INFO,FLOW` en `DIAG,KERN` aanwezig;
  - onafhankelijke paneelpersistentie aanwezig;
  - linker en rechter overlay-offset aanwezig;
- nieuwe ingebouwde selftest `T0ab` controleert de onafhankelijke panelen en de twee headerdropdowns.

Een volledige grafische Chromium-run kon in de container niet worden voltooid: de lokale headless Chromium-runtime bleef hangen door de bestaande container-/browserbeperkingen. De HTML-, CSS- en JavaScript-structuur is wel statisch en syntactisch gecontroleerd.
