# VortexLab v7.6.24a — decomposition-start hotfix

**Parent:** v7.6.24  
**Base solver lineage:** v7.5.3  
**Scope:** gerichte hotfix; geen wijziging van solverfysica, kandidaatregisters, scenario's of roadmap.

## Probleem in v7.6.24

De proxy-decompositie stopte bij het eerste `t=0`-checkpoint. In `analyzeRaw()` werd `intrinsicKinematics` opgenomen in de digest voordat de `const intrinsicKinematics`-declaratie was uitgevoerd. JavaScript plaatste de variabele daardoor in de temporal dead zone en wierp:

```text
ReferenceError: Cannot access 'intrinsicKinematics' before initialization
```

De gewone 10-run SPEC CLOCK-benchmark werd hierdoor niet geraakt; alleen decomposition-, continuum- en cross-knotruns faalden vóór hun eerste snapshot.

## Reparaties

### 1. Intrinsieke kinematica vóór digest

De volgorde is nu:

1. counterfactuals, Shapley, normalisaties en lengte-/κ-routes;
2. volledige intrinsieke rigid-rotationkinematica;
3. digest over alle resultaten.

Daarmee zijn `intrinsicKinematics.A/B.current/calibration` beschikbaar voordat de digest ze leest.

### 2. Expliciete fout- en abortlogging

Nieuwe ModelLog-events:

- `proxy-decomposition-error`
- `proxy-decomposition-abort`

Een foutrecord bevat:

- fase (`setup/t0-checkpoint` of `accepted-step-checkpoint`);
- scenario-id en label;
- checkpointindex en doeltijd;
- aantal voltooide en verwachte snapshots;
- foutmelding en stack;
- UTC-tijdstip.

De CLOCK-status toont voortaan de concrete foutmelding. Bij een fout wordt, wanneer auto-export actief is, ook automatisch een timestamped `proxy-error`-sessielog geëxporteerd.

### 3. Echte runtime-smoketest

De module-selftest bouwt nu synthetische calibratie- en actuele snapshots en voert werkelijk uit:

```text
analyzeRaw(smokeRaw, smokeCalibration)
```

De test vereist:

- pure analyse zonder modelmutatie;
- geldige 8-cijferige digest;
- eindige reconstructiefout;
- eindige intrinsieke `Ω`-vector, `Ω_parallel`, `|Ω|` en `|Ω_perp|` voor A/B en iso/mutual/full, actueel en calibratie.

De algemene `?selftest=1`-gate vereist voortaan `runtimeSmokePass=true`.

## Ongewijzigd

- 20 decomposition-scenario's;
- 49 verwachte snapshots;
- vijf Fourier/ideal embeddingparen;
- R24–R26 finite/applicable filtering;
- continuum- en holdoutformules;
- resizebare CLOCK-sidebar;
- automatische timestamped exports;
- roadmap v7.6.25–v7.7.0;
- RK4/CFL-, Biot–Savart-, BEM-, topology-guard- en stretch-gatefysica.

## Uit te voeren browsercontrole

Start:

```text
RUN → SST CLOCK · continuum + κ_geom + canonical embedding pairs
```

De eerste zichtbare voortgang moet direct `1/49` snapshots worden in plaats van een terugkeer naar `AFGEBROKEN · 0/49`.
