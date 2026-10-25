# VL11 — Ontwerp: cilinder- / eindcaps-BEM

Status: **ontwerpdoc klaar · wacht op ACK · geen code** · 2026-10-23

## Doel

Echte u·n = 0 op cilinderwand en eindcaps in het filamentlab. Onderscheid houden van bestaande knooptube Neumann-BEM/MFS (v7.5.2).

## Bestaande staat

- Tube-BEM: `BEM_SOURCE_MODEL='neumann-source-panel-mfs-v1'`
- Fluid-P2: wall impermeability = `NOT_IMPLEMENTED` / diagnostische samples only

## Ontwerpeisen

1. Discretisatie wand + caps; rebuild-cadans vs CFL
2. Residual-rapportage max |u·n|
3. Exclusiviteit / samenhang met `bgFlow`
4. Negatieve controle (bestaande SPEC BEM-negatieve test) behouden
5. Tube-BEM regressie groen

## Koppeling Fluid-P3 / VL13

Volledige druk-Poisson hoort bij VL13; VL11 mag een pure Neumann-correctie op het filament-superposed veld blijven.

## ACK-checklist

- [ ] Methodekeuze (BEM vs MFS vs panel) ACK
- [ ] Acceptatiedrempels ACK
- [ ] Implementatie mag starten
