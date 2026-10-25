---
name: VL10 lift falsificatie
overview: SST lift-/impulsflux-falsificatie op de bestaande bundel-splay; eerst ontwerpdocument met criteria vóór enige run.
todos:
  - id: design-doc
    content: Ontwerpdoc hypothese, observabelen, falsificatiecriteria, kinematische caveat
    status: completed
  - id: implement-after-ack
    content: Implementatie pas na ACK ontwerpdoc
    status: pending
isProject: false
---

# VL10 — Lift-falsificatie op de bundel

Parent: [VORTEXLAB_V7X_EPIC.plan.md](../complete/VORTEXLAB_V7X_EPIC.plan.md)

## Bron

- Stappenplan v6 §5 v7.5.1
- Stappenplan v4/v5 §3 item 11

## Status

**Status: ontwerpdoc klaar · wacht op ACK · geen code.**

Ontwerpdoc: [`05_apps/A003_vortexlab/docs/planning/VL10_lift_falsificatie_ontwerp.md`](../../../05_apps/A003_vortexlab/docs/planning/VL10_lift_falsificatie_ontwerp.md)

Splay/fluxmachinerie ligt in v7.4.2–v7.5.1; falsificatiecriteria staan in het ontwerpdoc; runner ontbreekt tot ACK.

## Wat bestaat al

- Ω_bundle(z), parallel/splay/periodic profielen.
- Fluxbehoud-tests T9a; rendering-onafhankelijkheid T9c; tekeninversie T9d.
- Eerlijkheidslabels: kinematische ansatz ≠ drukgesloten oplossing.

## Doel

(a) Hypothese als SST-claim: axiale gradiënt in bundeldichtheid ↔ lift/impulsflux; tekenwissel bij gradiëntomkering.  
(b) Observabelen: impulsflux per z-slab + filamentrespons testring.  
(c) Criteria vóór eerste run: tekenwissel onder λ-omkering; convergentie onder lijnverfijning; nul-effect bij parallel profiel als controle.  
(d) Caveat-veld in elke uitvoer-JSON zolang splay niet drukgesloten is.

## Implementatie

1. ~~Schrijf ontwerpdoc in `docs/planning/` of naast dit plan; ACK vereist.~~ → gedaan.
2. Runner + export; RESEARCH gates; geen post-hoc criteriumwijziging — **pas na ACK**.
3. Versie pas na ACK.

## Gates / acceptatie

- Ontwerpdoc ACK vóór code.
- JSON bevat `kinematicAnsatzCaveat=true` (of equivalent).
- Controle-scenario parallel → null effect binnen tolerantie.

## Tests

- T9c-hergebruik voor sampling-onafhankelijkheid.
- Nieuw T-set na implementatie.

## Versie

Na ACK: volgende v7.5.x / v7.6.x patch volgens impact.

## Buiten scope

Drukgesloten splay (VL13); cilinder-BEM (VL11).
