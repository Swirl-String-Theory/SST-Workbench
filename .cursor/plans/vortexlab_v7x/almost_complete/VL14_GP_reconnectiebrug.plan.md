---
name: VL14 GP reconnectiebrug
overview: Lokale GP-reconnectiebrug (Koplik–Levine) via ModelLog-Y-snapshots als koppelvlak.
todos:
  - id: design-doc
    content: Ontwerpdoc stop bij d≈4a, export, GP-doosje, filament-extractie, topologiegarantie
    status: completed
  - id: implement-after-ack
    content: Implementatie pas na ACK
    status: pending
isProject: false
---

# VL14 — GP-reconnectiebrug

Parent: [VORTEXLAB_V7X_EPIC.plan.md](../complete/VORTEXLAB_V7X_EPIC.plan.md) · Bij voorkeur na: [VL13](VL13_continuumsolver.plan.md) (of parallel na ontwerp als GP-stack los staat)

## Bron

- Stappenplan v6 §5 v7.5.5
- Stappenplan v4/v5 §3 item 8

## Status

**Status: ontwerpdoc klaar · wacht op ACK · geen code.**

Ontwerpdoc: [`05_apps/A003_vortexlab/docs/planning/VL14_GP_reconnectiebrug_ontwerp.md`](../../../05_apps/A003_vortexlab/docs/planning/VL14_GP_reconnectiebrug_ontwerp.md)

Topology guard stopt vóór doorsnijding; reconnectie is expliciet niet gemodelleerd (runtime messaging). Brugimplementatie wacht op ACK.

## Wat bestaat al

- ModelLog + Y-snapshots.
- Contactvloer max(3a, 64·ε·L_ref); topology guard first-hit bisectie.
- Geen numerieke reconnectie-acceptatie.

## Doel

Koplik–Levine-route: filamentrun stopt bij d ≈ 4a → export (ModelLog-Y natuurlijk koppelvlak) → GP-doosje door reconnectie → filamenten terugextraheren → optioneel hervatten.

## Implementatie

1. ~~Ontwerpdoc: file-/IPC-protocol, units, a_sim vs healing length, determinisme, falende extractie.~~ → gedaan.
2. Harde scheiding: browserfilament blijft free-filament tot brug expliciet wordt aangeroepen — **pas na ACK**.
3. Provenance: elke hervatting logt GP-engine versie + hashes.

## Gates / acceptatie

- Round-trip op gecontroleerd anti-parallel paar met bekende topology change.
- Mislukte extractie → FAIL, geen stille continue tunneling.
- Topology guard default blijft aan buiten brugvenster.

## Tests

- Contracttests op snapshot schema.
- Geen regressie op «geen reconnectie»-paden.

## Versie

Na ACK; eigen minor/major afhankelijk van koppeling.

## Buiten scope

Canonieke SST-klokwet; continuum Taylor-kolom tenzij hergebruikt als host.
