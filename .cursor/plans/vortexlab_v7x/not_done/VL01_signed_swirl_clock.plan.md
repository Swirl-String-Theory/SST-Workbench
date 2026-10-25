---
name: VL01 signed swirl clock
overview: Vervang de symmetrische RMS-envelope door een puntgewijze signed lokale Swirl-Clockroute (roadmap v7.6.26).
todos:
  - id: implement-veff
    content: Puntgewijze v_eff²(s) = |v↺* ê + u_mutual|²
    status: pending
  - id: report-metrics
    content: Signed mean, RMS, ±arclengthfracties, extrema, A/B- en chiraliteitspariteit
    status: pending
  - id: gates-ui-export
    content: ENGINE/RESEARCH gates + CLOCK-UI + schema-bump
    status: pending
isProject: false
---

# VL01 — Signed lokale Swirl-Clockroute (v7.6.26)

Parent: [VORTEXLAB_V7X_EPIC.plan.md](../complete/VORTEXLAB_V7X_EPIC.plan.md) · Blokkeert op: [VL00](VL00_baseline_reach.plan.md)

## Bron

- `VortexLab-roadmap-v7.6.25-v7.7.0.md` §v7.6.26
- Analyse v7.6.22 §12 v7.6.25 (zelfde inhoud, oudere nummering)

## Status

**Open.** Geen `v_eff` / signed-route markers in runtime. RMS-envelope blijft actief.

## Wat bestaat al

- Mutual tangent velocity en formele veldbracket (v7.6.5+).
- Proxy-decompositie met mutual-kanaal (v7.6.16+).
- Intrinsieke Ω-vector en carrier-as (v7.6.24).

## Doel

Puntgewijs:

$$
v_{\rm eff}^2(s)=\bigl|v_{\!\circlearrowleft}^{\ast}\hat{\mathbf e}(s)+\mathbf u_{\rm mutual}(s)\bigr|^2.
$$

Rapporteren: signed mean, RMS, positieve/negatieve arclengthfracties, extrema, A/B-pariteit, chiraliteit. Oude ±u_RMS-route blijft alleen symmetrische envelope.

## Implementatie

1. Passieve evaluatie op bevroren snapshots (geen solverfeedback).
2. Parallel export naast envelope; UI-label «signed local» vs «envelope».
3. Schema-bump op proxy-decomposition of apart signed-routeblok.
4. In-app roadmap-item v7.6.26 → ACTIEF na release.

## Gates / acceptatie

- Deterministische herhaalbaarheid.
- A/B-swap keert signed mean om volgens gemeten pariteit.
- Static-null: signed mean ≈ 0 binnen vaste tolerantie.
- Envelope blijft bit-vergelijkbaar met pre-VL01 op dezelfde snapshots.

## Tests

- Node/harnas op synthetische mutual velden.
- Selftest-marker voor signed-route aanwezigheid.
- Smoke: één decomposition-run met beide routes in export.

## Versie

`7.6.26`

## Buiten scope

Afstandsholdouts (VL02), Bishop-frame (VL04), canonieke klokwet.