---
name: VL04 bishop material frame
overview: Passief Bishop-frame per centerlinepunt met interne fasecoördinaat θ_int zonder solverfeedback (roadmap v7.6.29).
todos:
  - id: bishop-frame
    content: Per punt (t̂, n̂1, n̂2) Bishop-transport langs gesloten curve
    status: pending
  - id: theta-int
    content: "θ_int(s,t) met θ̇0 = ω_c = v↺*/r_c; geen externe modulatie"
    status: pending
  - id: frame-gates
    content: Orthogonaliteit, norm, holonomie, cyclic-index, resolutie, nul solverfeedback
    status: pending
isProject: false
---

# VL04 — Passief Bishop-material frame (v7.6.29)

Parent: [VORTEXLAB_V7X_EPIC.plan.md](../complete/VORTEXLAB_V7X_EPIC.plan.md) · Blokkeert op: [VL03](VL03_observable_separation.plan.md)

## Bron

- Roadmap §v7.6.29
- Analyse v7.6.22 §11.4 + §12 v7.6.28

## Status

**Open.** Geen Bishop-constructie of `theta_int` in runtime (roadmap-HTML noemt het woord alleen als toekomstitem).

## Wat bestaat al

- Centerline + arclength-parametrisatie uit decompositie.
- `OMEGA_COMPTON_SST` / horn-fasefrequentie als referentieconcept (niet automatisch r_c van het frame).
- UI-blok INTERNAL PHASE — NOT YET RESOLVED (na VL03).

## Doel

Per centerlinepunt:

$$
(\hat{\mathbf t},\hat{\mathbf n}_1,\hat{\mathbf n}_2),\qquad
\theta_{\rm int}(s,t),\qquad
\dot\theta_0=\omega_c=\frac{v_{\!\circlearrowleft}^{\ast}}{r_c}.
$$

Nog geen externe modulatie of terugkoppeling naar de filament-ODE.

## Implementatie

1. Parallel transport / Bishop langs discrete polygon; periodieke holonomie rapporteren.
2. Passieve integratie van θ_int langs tijdcheckpoints.
3. Expliciete keuze/documentatie van r_c (a_sim vs r_kern vs R_horn) — default mag niet stilzwijgend R_horn zijn.
4. Vul UI-blok INTERNAL PHASE met frame-diagnostics; koppel nog geen transfer law.

## Gates / acceptatie

- Orthogonaliteit en eenheidsnorm binnen tolerantie.
- Gesloten-loop-holonomie eindig en stabiel onder N.
- Initial-phase-invariantie en cyclic-index-invariantie.
- Snapshot-purity: analyse muteert Y/tPhys niet.

## Tests

- Synthetische cirkel: holonomie ≈ 0 (of bekende solid-angle/twist-conventie, gedocumenteerd).
- Trefoil N-ladder: frame-residu niet groeiend.
- Selftest: solverfeedback-hash ongewijzigd.

## Versie

`7.6.29`

## Buiten scope

Gradienttensor (VL05), afgeleide δθ̇-wetten (VL06).