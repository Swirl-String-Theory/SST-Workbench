---
name: VL12 feynman pinning
overview: Discrete Feynman-roostertest plus vortex-wand-pinning; completeert audit-item 14 samen met v7-wrijving.
todos:
  - id: design-doc
    content: Ontwerpdoc ⟨ω_z⟩=2Ω, n_v=2Ω/κ, b_△∝Ω^{-1/2}, pinning; Tkachenko buiten scope
    status: completed
  - id: implement-after-ack
    content: Implementatie pas na ACK
    status: pending
isProject: false
---

# VL12 — Feynman-rooster + pinning

Parent: [VORTEXLAB_V7X_EPIC.plan.md](../complete/VORTEXLAB_V7X_EPIC.plan.md) · Bij voorkeur na: [VL11](VL11_cilinder_bem.plan.md)

## Bron

- Stappenplan v6 §5 v7.5.3
- Stappenplan v4/v5 §3 item 10

## Status

**Status: ontwerpdoc klaar · wacht op ACK · geen code.**

Ontwerpdoc: [`05_apps/A003_vortexlab/docs/planning/VL12_feynman_pinning_ontwerp.md`](../../../05_apps/A003_vortexlab/docs/planning/VL12_feynman_pinning_ontwerp.md)

Bundel levert coarse-grained helft (n_v, N_phys in verslagen); discrete roostertest en wand-pinning wachten op ACK + implementatie.

## Wat bestaat al

- Wrijving α/α′ (v7) als eerste helft audit-item 14.
- Bundel sampling + Ω_core read-only firewall.
- Cilindercontext (na VL11 sterker).

## Doel

- ⟨ω_z⟩ = 2Ω-check tegen samplingveld.
- n_v = 2Ω/κ, b_△ ∝ Ω^(−1/2).
- Vortex-wand-pinning.
- Tkachenko/defecten expliciet buiten scope (zoals bundelverslag §6.2).

## Implementatie

1. ~~Ontwerpdoc met meetprotocollen en eerlijkheidsgrenzen (representatieve sampling ≠ 10⁷ kernlijnen).~~ → gedaan.
2. Passieve of semi-passieve diagnostics eerst; pinning-dynamica alleen met expliciete modelclaim — **pas na ACK**.
3. Sluit audit-item 14 in docs wanneer gates groen zijn.

## Gates / acceptatie

- Schalingsregressie b_△ vs Ω binnen tolerantie op ankergrid.
- Pinning: gedocumenteerde acceptatiecriteria in ontwerpdoc.
- Geen claim op Tkachenko.

## Tests

- Nieuw T-set na implementatie; bundel T9-regressie blijft groen.

## Versie

Na ACK.

## Buiten scope

Continuum Taylor-kolom (VL13); reconnectie (VL14).
