---
name: VL05 velocity gradient tensor
overview: Externe mutual velocity-gradienttensor G met strain/vorticity-splitsing en convergentiegates (roadmap v7.6.30).
todos:
  - id: compute-G
    content: "G_ij = ∂_j u_mutual,i; S=(G+Gᵀ)/2; W=(G−Gᵀ)/2"
    status: pending
  - id: projections
    content: "Rapporteer t̂ᵀ S t̂ en ω_ext·t̂; correlatie met rigid response"
    status: pending
  - id: gradient-gates
    content: tr G≈0, stencil-, parameterisatie- en resolutieconvergentie
    status: pending
isProject: false
---

# VL05 — Externe velocity-gradienttensor (v7.6.30)

Parent: [VORTEXLAB_V7X_EPIC.plan.md](../complete/VORTEXLAB_V7X_EPIC.plan.md) · Blokkeert op: [VL04](VL04_bishop_material_frame.plan.md)

## Bron

- Roadmap §v7.6.30
- Analyse v7.6.22 §12 v7.6.29

## Status

**Open.** Geen G_ij / strain-export in runtime.

## Wat bestaat al

- Direct mutual Biot–Savart veld per snapshot.
- Bishop-frame uit VL04 voor lokale projecties.
- Intrinsieke rigid-rotationrespons.

## Doel

$$
G_{ij}=\partial_j u_{{\rm mutual},i},\quad
S=\tfrac12(G+G^T),\quad
W=\tfrac12(G-G^T).
$$

Gates voor incompressibiliteit (tr G≈0), stencilconvergentie, parameterisatie en resolutie. Projecties \(\hat{\mathbf t}^TS\hat{\mathbf t}\) en \(\boldsymbol\omega_{\rm ext}\cdot\hat{\mathbf t}\).

## Implementatie

1. Eindige-differentiestencil op centerline-nbh of analytische kernel-afgeleide indien beschikbaar; keuze documenteren.
2. Cache G per checkpoint; geen dynamica-mutatie.
3. Export + UI onder RIGID / INTERNAL PHASE diagnostics.
4. Correlatie-tabel vs `omegaRigidCenterline` (informatief).

## Gates / acceptatie

- Median |tr G| onder vaste drempel op divergence-free testvelden.
- Stencil-halvering verandert projecties &lt; afgesproken %.
- Resolutieladder laatste paar &lt; 5% op primaire projecties.

## Tests

- Synthetisch star lichaam / bekende shear.
- Decomposition-smoke met G-blok in JSON.
- `npm run check`

## Versie

`7.6.30`

## Buiten scope

Bevriezen van δθ̇-wetten (VL06); continuum-PDE (VL13).