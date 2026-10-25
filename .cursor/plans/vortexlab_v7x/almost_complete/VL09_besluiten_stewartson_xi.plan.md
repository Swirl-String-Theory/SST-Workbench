---
name: VL09 besluiten stewartson xi
overview: Formeel vastleggen van Stewartson-eindbesluit en de ξ↔r_kern-conventiecheck als gate voor Track-B Δ-label.
todos:
  - id: stewartson-record
    content: "Besluit A (Ekman/HVBK) of B (definitief visueel) schriftelijk vastleggen; UI/docs sync"
    status: completed
  - id: xi-rkern-check
    content: "Documenten-/afleidingscheck ξ↔r_kern; Track-B label conditioneel houden of verwijderen"
    status: pending
isProject: false
---

# VL09 — Besluiten Stewartson + ξ↔r_kern

Parent: [VORTEXLAB_V7X_EPIC.plan.md](../complete/VORTEXLAB_V7X_EPIC.plan.md)

## Bron

- Stappenplan v4/v5 §2 item 5 (Stewartson), §5 item 16 (a↔ξ)
- Stappenplan v6 §4 (coreFlowLock half genomen — **DONE** elders)
- Release notes v7.5.1 (brug hernoemd naar ξ↔r_kern)

## Status

**Docs geschreven · waiting ACK Omar.** Formeel besluitmemo: [`docs/planning/VL09_besluit_stewartson_en_xi_rkern.md`](../../05_apps/A003_vortexlab/docs/planning/VL09_besluit_stewartson_en_xi_rkern.md) (2026-10-23). Stewartson = **Optie B** (geometrische visualisatie; \(q_S\) blijft; geen kwantitatieve Ekman-sluiting). Track-B Δ blijft **conditioneel** tot χ-fase package checklist PASS — label niet verwijderd. `coreFlowLock` default false is **afgerond** (niet opnieuw beslissen).

## Wat bestaat al

- Stewartson-visuals + q_S-proxy (geen kwantitatieve Ekman-sluiting).
- GP-Δ keuzepaneel: Roberts–Grant default; Track-B conditioneel.
- R_horn / r_kern / a_sim scheiding.

## Doel

1. **Stewartson:** Optie A = dimensioneel gesloten E=ν/(ΩL²) als aparte modeluitbreiding; Optie B = definitief geometrische visualisatie, q_S blijft, kwantitatieve ambitie geschrapt. Vastleggen in `docs/` + changelog.
2. **ξ↔r_kern:** Documentcheck in χ-fasepakket / Canon: is a in U=Γ/(4πR)[ln(8R/a)−Δ] dezelfde ξ-definitie als Track-B kern-ODE? Gate om «conditioneel»-label te mogen verwijderen.

## Implementatie

1. Kort besluitmemo onder `05_apps/A003_vortexlab/docs/` (of Canon-pad indien elders).
2. Bij B: UI-copy aanscherpen; geen nieuwe codepaden.
3. Bij A: nieuw subplan aftakken (buiten VL13 tenzij HVBK daar hoort).
4. Track-B: label updaten alleen na geslaagde check.

## Gates / acceptatie

- Memo met datum, keuze, handtekening/ACK Omar.
- Geen stille verwijdering van «conditioneel» zonder check-PASS.

## Tests

- Geen codevereiste bij B + open ξ-check.
- Selftest ongewijzigd tenzij labels/DOM wijzigen.

## Versie

Docs-only of patch-label sync; geen scientific version bump zonder A-implementatie.

## Buiten scope

Implementatie Ekman/HVBK (apart); lift/BEM/continuum.
