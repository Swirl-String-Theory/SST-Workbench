# VortexLab v7.6.24b

## Doel

Gerichte hotfix bovenop v7.6.24a voor twee onafhankelijke problemen:

1. cross-knotholdouts stopten bij Fourier `5_2`, omdat de legacy lab-z-faseproxy een vrijwel nul zijnde geïsoleerde Ω-projectie als fatale kalibratiefout behandelde;
2. alle gegenereerde info-iconen toonden naast de eigen tooltip ook de native browsertekst `Toelichting`, waardoor beide lagen elkaar overlapten.

Daarnaast is de passieve Rosetta-schaalprobe uitgebreid met expliciete Planck-radius/diameterpresets.

## 1. Projection-null-safe cross-knotholdouts

De gewone SPEC CLOCK-benchmark blijft streng op de legacy lab-z-route.

Alleen scenario's met `knotSource` gebruiken nu:

```js
calibrateSpecClockPhase({
  mode: 'intrinsic-holdout',
  allowProjectionNull: true
})
```

Wanneer de legacy fractionele projectie niet eindig is, maar de volledige en geïsoleerde Ω-metingen wel eindig zijn, geldt voortaan:

```text
VALID · NON-INFORMATIVE FOR LEGACY LAB-Z PROJECTION
```

De run gaat dan door. De confirmatoire cross-knotanalyse blijft gebaseerd op de volledige intrinsieke rigid-rotationvector en haar projecties.

De toestand wordt expliciet gelogd met:

- `mode: intrinsic-holdout`;
- `projectionNull: true`;
- `legacyProjectionInformative: false`.

Een werkelijk ontbrekende of niet-eindige Ω-meting blijft wel fataal.

## 2. Planckpresets voor `a_probe`

Toegevoegd:

- `Planck · ℓ_P/2 (radius-audit)`;
- `Planck · ℓ_P`;
- `Planck · 2ℓ_P (diameter-audit)`.

De probe blijft strikt metadata-only. Zij wijzigt niet:

- `a_sim`;
- `r_kern`;
- `R_horn`;
- circulatie;
- BEM;
- contactdetectie;
- filamentintegrator.

`R_horn` blijft afzonderlijk de canonieke SST circulatie-/envelopschaal. De drie Planckvarianten zijn bedoeld als Rosetta/String-schaalaudit en voorkomen dat een radius/diameterconventie stilzwijgend wordt gekozen.

## 3. Tooltipcorrectie

De gegenereerde info-iconen krijgen niet langer:

```html
title="Toelichting"
```

Daardoor verschijnt geen tweede native browsertooltip meer. De eigen inhoudelijke VortexLab-tooltip blijft behouden voor hover, focus en klik.

Deze wijziging geldt globaal voor alle automatisch gegenereerde info-iconen.

## 4. Ongewijzigd

- solverfysica;
- SST-constanten;
- `R_horn`;
- `a_sim`;
- candidate registry;
- continuumfits;
- R24–R31-logica;
- canonicalized embeddings;
- scenarioaantal: 20;
- verwachte snapshots: 49;
- timestamped auto-export.

## Verwachte verificatie

Start in CLOCK:

```text
Run continuum + κ_geom + cross-knot holdouts
```

De eerdere abort bij `holdout-fseries-5_2` hoort niet terug te keren. De run hoort door te lopen tot `20/20` en `49/49 snapshots`, tenzij een andere werkelijke meetfout optreedt.
