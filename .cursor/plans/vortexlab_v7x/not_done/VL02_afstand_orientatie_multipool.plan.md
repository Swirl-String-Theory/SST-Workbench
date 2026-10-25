---
name: VL02 afstand orientatie multipool
overview: Bevroren geometrie-matrix voor afstand, laterale offset, kanteling, co/contra-oriëntatie en spiegeling (roadmap v7.6.27).
todos:
  - id: freeze-scenarios
    content: "Preregistreer d/L_K=1.1,1.25,1.5,2,3,4 + offset/tilt/oriëntatie/spiegel; reserveer holdouts"
    status: pending
  - id: runner-metrics
    content: Meet u_mutual, Ω_rigid, ∇u_mutual, δlnR_directed per scenario
    status: pending
  - id: holdout-gates
    content: HoldoutPass verplicht; geen kandidaatselectie op dezelfde set
    status: pending
isProject: false
---

# VL02 — Afstand, oriëntatie en multipolen (v7.6.27)

Parent: [VORTEXLAB_V7X_EPIC.plan.md](../complete/VORTEXLAB_V7X_EPIC.plan.md) · Blokkeert op: [VL01](VL01_signed_swirl_clock.plan.md)

## Bron

- Roadmap §v7.6.27
- Analyse v7.6.22 §12 v7.6.26

## Status

**Open.** Bestaande A–B afstand (`Δz_AB,0`) en cross-knot holdouts dekken niet de volle multipool-/oriëntatiematrix.

## Wat bestaat al

- Instelbare axiale A–B afstand (v7.6.6+).
- Canonicalized embeddings + Fourier/ideal paren (v7.6.24).
- Signed route-metrics uit VL01 (vereist).

## Doel

Bevroren geometrieën voor \(d/L_K \in \{1.1,1.25,1.5,2,3,4\}\), plus laterale offset, kantelhoek, co-/contraoriëntatie, gespiegeld trefoil, achirale figure-eight. Ongeziene scenario’s als holdout reserveren vóór runs.

## Implementatie

1. Scenario-register met `holdout: true|false` bevroren vóór eerste run.
2. Passieve runner (geen dynamische drift tenzij expliciet gelabeld).
3. Export per cel: `u_mutual`, `Ω_rigid` (intrinsiek), optioneel `∇u` stub tot VL05, `δlnR_directed` uit VL01.
4. UI: selecteerbare matrix + holdout-badge.

## Gates / acceptatie

- HoldoutPass verplicht voor confirmatoire claims.
- Geen κ-kandidaat `accepted` op trainingscellen alleen.
- Deterministische JSON bij herhaalde freeze.

## Tests

- Selftest: register bevat alle zes d/L_K en minstens één gereserveerde holdout.
- Smoke: subset Snel (1.1, 2, 4) + één tilt.

## Versie

`7.6.27`

## Buiten scope

Observable hernoemingen (VL03), gradienttensor-implementatie (VL05).
