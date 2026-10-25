# VL10 — Ontwerp: lift-falsificatie op de bundel

Status: **ontwerpdoc klaar · wacht op ACK · geen code** · 2026-10-23

## Hypothese (SST-claim, research track)

Een axiale gradiënt in coarse-grained bundeldichtheid n_v(z) induceert een netto impulsflux / liftrespons van een testfilament; omkering van de gradiënt (λ → 1/λ) keert het teken van de observabele om.

## Observabelen

1. Impulsflux per z-slab uit het coarse-grained bundelveld
2. Filamentrespons (Δp_z of equivalent) van een testring in de bundel
3. Controlescenario: parallel profiel → nul-effect

## Falsificatiecriteria (vóór eerste run)

| ID | Eis |
|----|-----|
| F1 | Tekenwissel onder λ-omkering |
| F2 | Convergentie onder lijnverfijning (T9c-hergebruik) |
| F3 | Parallel-profiel controle: |effect| < drempel |
| F4 | Elke JSON bevat `kinematicAnsatzCaveat=true` |

## Eerlijkheidsgrenzen

Splay is een kinematische ansatz, geen drukgesloten Euler/HVBK-oplossing. Resultaten zijn conditioneel op die ansatz.

## Koppelvlak

Bestaande `bundleProfile` / splay / Ω_bundle(z); exclusiviteit met wall bgFlow (v7.4.2+).

## ACK-checklist

- [ ] Hypotheseformulering ACK
- [ ] F1–F4 drempels numeriek vastgelegd
- [ ] Implementatie mag starten
