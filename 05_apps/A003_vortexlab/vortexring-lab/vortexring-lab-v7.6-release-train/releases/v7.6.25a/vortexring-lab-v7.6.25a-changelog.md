# VortexLab v7.6.25a

Parent: `v7.6.25`  
Base lineage: `v7.5.3`  
Scope: reach/DCSD-validatiecorrectie; geen wijziging van filamentdynamica of Swirl-Clockfysica.

## Correcties

### 1. Reachrunner gebruikt werkelijk de holdoutselectie

De reachrunner las in v7.6.25 niet-bestaande IDs (`cSpecSourceIdeal`, `cSpecSourceFseries`, `cSpecSourceKnotplot`). Optional chaining zette daardoor alle bronnen stilzwijgend op `false`, terwijl de topologielijst wel gevuld bleef.

V7.6.25a gebruikt nu rechtstreeks `SpecClockProxyDecomposition.readKnotSelection()` en valt alleen terug op de bestaande `cSpecHoldout*`-controls. Ideal-, Fseries- en KnotPlot-geometrieën worden daardoor volgens exact dezelfde selectie uitgevoerd als de holdouts.

### 2. Rank-deficiënte DCSD-verfijning

De ontkoppelde fallback voor bijna-singuliere 2×2-Jacobianen is vervangen door gedempte least-squares:

\[
(J^{\mathsf T}J+\lambda I)\,\delta
=-J^{\mathsf T}F.
\]

De solver probeert een gewone Newtonstap wanneer de Jacobiaan voldoende goed geconditioneerd is en meerdere Levenberg–Marquardt-schalen bij rank-deficiënte critical manifolds, zoals de antipodale DCSD-familie van een cirkel. Iedere kandidaatstap krijgt een residu-gebaseerde line search.

De acceptatiegrens voor opgeslagen DCSD-oplossingen is aangescherpt tot `5e-9`; G3 blijft beslissen op `1e-8`. G3 controleert nu de beste self- én inter-componentoplossingen, niet alleen de branch die toevallig de uiteindelijke reach begrenst.

### 3. Niet-vacuüm catalogusgates

Nieuwe gate `G4a` controleert dat een geselecteerde catalogusbron ook werkelijk resultaten heeft geproduceerd.

- geselecteerde catalogus, nul catalogusrows → `ENGINE FAIL`;
- geen catalogus geselecteerd → `NOT_APPLICABLE`;
- geselecteerde Ideal-data, nul Ideal-rows → G4 `FAIL` en R41 `BLOCKED`;
- R41 kan daardoor niet meer vacuüm `PASS` of generiek `INFO` rapporteren.

### 4. SPARK/HUD-wrapperherstel

Alle vier onderste widgets worden via één idempotente `vlEnsureBottomWidget()` opgebouwd:

- LIVE STABILITEIT;
- SPEC CLOCK · SNEL;
- STATS;
- SPARK.

Een bestaande wrapper wordt hergebruikt en naar de juiste container teruggezet; een ontbrekende wrapper wordt opnieuw opgebouwd. Voor SPARK bestaat bovendien een fallback via de parent van `#cspark`.

De summary-click is nu expliciet: gesloten opent met één klik, geopend blijft bij één klik open, dubbelklik wisselt open/dicht. Dragged clicks blijven onderdrukt.

### 5. Zelftestcorrecties

- decomposition-schema verwacht nu `/2.1` in plaats van verouderd `/2.0`;
- `cSpecAutoExport` krijgt zowel `dataset.bound` als `dataset.specBound`;
- HUD-test controleert de vier vereiste widgetsoorten afzonderlijk;
- reach-kerneltest heet nu `T0e25a`.

### 6. Workflowmigratie

De nieuwe sessiesleutel is `vortexlab.clock.workflow.7.6.25a` met automatische fallback naar `vortexlab.clock.workflow.7.6.25`. Eerder behaalde ENGINE-ontgrendelingen in hetzelfde browsertabblad blijven daardoor behouden.

## Bewust ongewijzigd

Byte-identiek aan v7.6.25:

- `velocityCore`;
- `velAll`;
- `rk4Step`;
- `topologyClearance`;
- `intrinsicCoreRadiusLimit`;
- de oude `approximateDoublyCriticalDistance`-legacydiagnostiek.

De continue reach blijft passief en schrijft niets terug naar `a_sim`, `r_kern`, `R_horn`, topology guard of de integrator.

## Validatie

- inline JavaScript syntax: PASS;
- statische DOM-ID-uniciteit: PASS;
- exacte cirkel N=64–768: maximaal DCSD-orthogonaliteitsresidu `2.31e-14`;
- splinecirkel N=256: residu `1.12e-16`;
- twee-cirkelanker: reach `0.4`, limiter `INTER_COMPONENT`;
- Ideal `3:1:1` N=64: self-radius `0.4999852`, residu `5.75e-16`;
- KnotPlot `Tlink_6_9` N=64: inter-componentradius `0.5017031`, residu `6.44e-14`;
- patch clean-apply en exacte reproductie: PASS;
- volledige interactieve WebGL/DOM-zelftest kon niet headless worden uitgevoerd doordat Chromium in deze container vóór DOM-export blijft hangen.

## Lokaal opnieuw uitvoeren

Alleen deze twee acties zijn noodzakelijk:

1. `🧪` zelftest;
2. `Continue reach/DCSD` met profiel **Standaard** en de gewenste Ideal/Fseries/KnotPlot-selectie.

De eerdere SPEC-, decomposition-, holdout- en continuumexports uit v7.6.25 blijven inhoudelijk bruikbaar.
