# VortexRing Lab 7.6 release train

Deze release train beëindigt de reeks onderling verschillende bestanden die allemaal `v7.5.4` heetten. Iedere cumulatieve featurelaag heeft nu een unieke patchversie.

## v7.6.0 — Geconsolideerde z-flow/potential-flow- en paired-docks-basis
Parent: `7.5.4-zflow-header-paired-docks`
- Achtergrondstroomlijnen en potential-flow refereren aan de wereld-z-as.
- Potential-flow/Cp-diagnostiek en Neumann/BEM-functionaliteit behouden.
- Simulatiesnelheid, pauze, presets en view-bediening in de topbar.
- Gekoppelde FLOW/CILINDER- en VORTEX/KERN-docks.

## v7.6.1 — Gilbert ideal/tight- en standaard .fseries-catalogi
Parent: `7.6.0`
- Volledige Gilbert ideal/tight-database met 34 configuraties.
- 78 compacte .fseries-geometrieën toegevoegd als niet-automatisch-ideale catalogus.
- Automatische detectie van Fourier-indexconventie j=0 versus j=1.
- Bron/provenance en cataloguswaarschuwingen toegevoegd.

## v7.6.2 — Aparte .fseries-dropdown
Parent: `7.6.1`
- Gilbert ideal/tight en .fseries staan in afzonderlijke selectors.
- Catalogusselecties zijn wederzijds exclusief.
- Terminologie aangepast naar catalogusobject/catalogusvorm.

## v7.6.3 — Simulatoroverlays en SST-diagnostiekverplaatsing
Parent: `7.6.2`
- Topology/contactmeldingen onder de topbar geplaatst.
- LIVE STABILITEIT, geometriekaarten en cspark als permanente onderste simulatoroverlays.
- SST chi-fase en vortex-stretching gate naar DIAG verplaatst.
- Overlaypositie volgt de geopende linker sidebar.

## v7.6.4 — Vlakke diagnostiekstructuur
Parent: `7.6.3`
- GEOMETRISCHE DIAGNOSTIEK is een vaste sectie in plaats van een collapsible.
- SST chi-fase en vortex-stretching gate zijn zelfstandige sibling-collapsebles.
- Onlogische geneste collapsible-structuur verwijderd.
- Zelftests aangepast aan de nieuwe DOM-structuur.

## v7.6.5 — Speculative swirl-clock A↔B
Parent: `7.6.4`
- Expliciet gewaarschuwde Research-Track-module zonder solverkoppeling.
- Veldroute via wederzijdse tangentiële Biot-Savart-snelheid.
- Onafhankelijke faseproxy via body-fasefrequentie en vaste kalibratie.
- Closure-envelop, klokresidu en accumulated lag toegevoegd.

## v7.6.6 — Instelbare initiële A-B-afstand
Parent: `7.6.5`
- Nieuwe regeling voor axiale startafstand Delta z_AB,0.
- Symmetrische plaatsing van A en B rond het middenvlak.
- Totale centrumafstand, actuele afstand, clearance en stopgrens zichtbaar.
- Afstandswijziging reset geometrie en wist bewust fasekalibratie.

## v7.6.7 — Sweep-preset, quick-controls, overlay en tekstlogging
Parent: `7.6.6`
- Nieuwe SST speculative swirl-clock sweep-preset.
- Delta z_AB,0, Delta x(B), v_z(A) en v_z(B) gekloond naar het speculative paneel.
- Knoppen voor nadering en verwijdering van de twee dragers.
- Compacte SPEC CLOCK QUICK-overlay op de simulator.
- Automatische ModelLog-registratie en export naar log.txt naast JSON.

## v7.6.8 — Runtime bootstrap hotfix
Parent: `7.6.7`
- Herstelt het zwarte canvas/HUD-only startupdefect.
- Verwijdert de `ModelLog` temporal-dead-zone referentie uit de eerste `syncUi()`-passage.
- Publiceert `ModelLog` veilig als `window.ModelLog` na initialisatie.
- Toont vroege bootstrap- en ontbrekende THREE.js-fouten expliciet in de meldingsbalk.
- `v7.6.7` is wegens deze regressie niet de aanbevolen release.

## v7.6.9 — Spec-clock proxysemantiek en stabiele overlay
Parent: `7.6.8`
- Classificeert ruwe fase/veld-overlap of -afwijking niet langer als fysische closure of falsificatie.
- Legt vast dat een interne fase-observable en overdrachtswet tussen beide proxies nog ontbreken.
- Toont de quick-overlay alleen bij een actieve speculative-clockdiagnose.
- Werkt de overlay incrementeel bij zonder het volledige HTML-subtree per sample te reconstrueren.
- Voegt regressietests T0r en T0s toe voor niet-falsifiërende semantiek en stabiele DOM-identiteit.

## v7.6.10 — Vrije afstand en werkelijk gebonden spec-clockbediening
Parent: `7.6.9`
- Scheidt het vrije numerieke afstandsveld van de op cilinderhoogte begrensde slider.
- Voorkomt dat live synchronisatie een actief invoerveld tijdens typen overschrijft.
- Bindt alle spec-clockquick-velden en -knoppen daadwerkelijk aan MODEL en ModelLog.
- Schakelt periodieke z-wrapping automatisch uit voor startafstanden buiten de cilinderhoogte.
- Breidt ModelLog en de zelftests uit met afstand, offset, drift en grensstatus.
