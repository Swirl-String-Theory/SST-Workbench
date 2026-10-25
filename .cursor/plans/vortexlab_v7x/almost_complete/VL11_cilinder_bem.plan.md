---
name: VL11 cilinder BEM
overview: Upgrade van volume-only / tube-BEM naar echte u·n=0 op cilinderwand en eindcaps in het filamentmodel.
todos:
  - id: design-doc
    content: Ontwerpdoc cilinder+caps BEM vs bestaande knooptube-BEM; koppeling Fluid-P3
    status: completed
  - id: implement-after-ack
    content: Implementatie pas na ACK
    status: pending
isProject: false
---

# VL11 — Cilinder- / eindcaps-BEM

Parent: [VORTEXLAB_V7X_EPIC.plan.md](../complete/VORTEXLAB_V7X_EPIC.plan.md) · Bij voorkeur na: [VL10](VL10_lift_falsificatie.plan.md)

## Bron

- Stappenplan v6 §5 v7.5.2
- Stappenplan v4/v5 §3 item 9
- Fluid-P2 README: `NO_BOUNDARY_SOLVER` / wall impermeability unresolved

## Status

**Status: ontwerpdoc klaar · wacht op ACK · geen code.**

Ontwerpdoc: [`05_apps/A003_vortexlab/docs/planning/VL11_cilinder_bem_ontwerp.md`](../../../05_apps/A003_vortexlab/docs/planning/VL11_cilinder_bem_ontwerp.md)

Knooptube Neumann-BEM/MFS bestaat (v7.5.2, `bundleBEM*`). Cilinderwand + caps u·n=0 ontbreekt tot na ACK; P2 rapporteert bewust UNRESOLVED.

## Wat bestaat al

- `BEM_SOURCE_MODEL='neumann-source-panel-mfs-v1'` rond gesloten knooptube.
- Periodieke wall-normal samples als diagnostiek (geen oplegging).
- Potential-flow / Cp UI uit v7.6.0-lijn.

## Doel

Echte no-penetration op cilinder en bol/caps in het filamentlab, zodat «passieve cilinder» (Ω_wall=0, volume-only) wordt opgewaardeerd. Onderscheid houden met tube-BEM.

## Implementatie

1. ~~Ontwerpdoc: discretisatie, rebuild-cadans, CFL-impact, exclusiviteit met bgFlow, validatieankers.~~ → gedaan.
2. Negatieve controle behouden (bestaande BEM-negatieve SPEC-clocktest) — **pas na ACK**.
3. Fluid-qualification status van UNRESOLVED → gekwalificeerde reststatus alleen na gates.

## Gates / acceptatie

- max |u·n| op wand/caps onder drempel op ankerstromingen.
- Geen stille oplegging zonder residual-rapportage.
- Tube-BEM regressie groen.

## Tests

- Uitbreiding `test-fluid-qualification.mjs` na implementatie.
- Browser-smoke met BEM aan/uit.

## Versie

Na ACK; waarschijnlijk major research patch.

## Buiten scope

Volledige 3D Euler continuum (VL13); GP-reconnectie (VL14).
