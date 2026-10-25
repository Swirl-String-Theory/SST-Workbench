---
name: VL13 continuumsolver
overview: Roterende incompressibele continuumsolver (∇·u=0, Coriolis, drukprojectie, no-penetration) — enige route naar fysische Taylor-kolom/separatrix; dekt ook Fluid-P3.
todos:
  - id: design-doc
    content: Ontwerpdoc grid, projectie, BC, koppeling filamentlab, validatieankers
    status: completed
  - id: implement-after-ack
    content: Implementatie pas na ACK; waarschijnlijk apart package/worker
    status: pending
isProject: false
---

# VL13 — Roterende continuumsolver (Fluid-P3)

Parent: [VORTEXLAB_V7X_EPIC.plan.md](../complete/VORTEXLAB_V7X_EPIC.plan.md) · Bij voorkeur na: [VL12](VL12_feynman_pinning.plan.md)

## Bron

- Stappenplan v6 §5 v7.5.4
- Stappenplan v4/v5 §3 item 7
- Fluid-P2: pressure Poisson / cylindrical impermeability / Euler closure UNRESOLVED

## Status

**Status: ontwerpdoc klaar · wacht op ACK · geen code.**

Ontwerpdoc: [`05_apps/A003_vortexlab/docs/planning/VL13_continuumsolver_ontwerp.md`](../../../05_apps/A003_vortexlab/docs/planning/VL13_continuumsolver_ontwerp.md)

Filamentlab kan Taylor-kolom/separatrix principieel niet fysisch sluiten. P2 diagnostics bestaan zonder oplegging. Continuumimplementatie wacht op ACK.

## Wat bestaat al

- Filament + bgFlow wall/bundle.
- Diagnostische ∇·u samples en wall |u·n|.
- Tube-BEM; cilinder-BEM gepland in VL11.

## Doel

∇·u = 0, Coriolis, drukprojectie, echte no-penetration op cilinder en bol. Enige route naar fysische Taylor-kolom/separatrix. Fluid-P3-eisen (onafhankelijke Euler-referentie, pressure Neumann-compatibiliteit, vorticity-curl/invariant parity) horen hier.

## Implementatie

1. ~~Groot ontwerpdoc: numerieke methode, SI-units, CFL, koppelvlak met browser (EngineClient / SSTcore-adapter).~~ → gedaan.
2. Waarschijnlijk native/worker; niet alles in monoliet-HTML — **pas na ACK**.
3. Filamentlab blijft beschikbaar als vergelijkings-/inbeddingslaag.

## Gates / acceptatie

- Ankerstromingen (Taylor-Couette-achtig / kolom) met gedocumenteerde fouten.
- Geen PASS op filament-proxy alsof continuum gesloten is.
- P2-statuses promoveren alleen met bewijs.

## Tests

- Apart testpakket; `npm run check` blijft filament-P2 dekken tot integratie.

## Versie

Eigen major research track (niet per se 7.6.x patch).

## Buiten scope

GP-reconnectie (VL14); Swirl-Clock canonieke wet (VL07).
