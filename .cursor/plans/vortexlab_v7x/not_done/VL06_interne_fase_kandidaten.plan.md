---
name: VL06 interne fase kandidaten
overview: Bevries en test afgeleide interne-fasekandidaten pas na validatie van materiaalframe en gradienttensor (analyse v7.6.30).
todos:
  - id: preregister
    content: Bevries rotatie- en Kelvin/strain-formules vóór nieuwe runs; verbied post-hoc 1/(8π)
    status: pending
  - id: evaluate
    content: Evalueer kandidaten op VL01–VL05 pipelines
    status: pending
  - id: no-solver-couple
    content: Geen solverkoppeling; RESEARCH status apart van ENGINE
    status: pending
isProject: false
---

# VL06 — Afgeleide interne-fasekandidaten (v7.6.31)

Parent: [VORTEXLAB_V7X_EPIC.plan.md](../complete/VORTEXLAB_V7X_EPIC.plan.md) · Blokkeert op: [VL05](VL05_velocity_gradient_tensor.plan.md)

## Bron

- Analyse v7.6.22 §12 v7.6.30 (afgeleide kandidaten)
- Roadmap v7.7.0-precondities

## Status

**Open.** Geen geregistreerde interne-fasewet. κ_geom-kandidaten uit v7.6.22 zijn high-res inadmissible.

## Wat bestaat al

- Bishop θ_int (VL04), G/S/W (VL05), signed route (VL01), afstandsholdouts (VL02).
- κ_geom-registry (screening only; R27 FAIL-logica sinds v7.6.23).

## Doel

Pas na frame+gradient-validatie kandidaten preregistreren, o.a.:

- Rotatie: \(\delta\dot\theta_{\rm int}=\boldsymbol\omega_{\rm ext}\cdot\hat{\mathbf t}\).
- Kelvin/strain: alleen met expliciet finite-core-profiel \(\mathcal F_K(S,a_{\rm core},\Gamma,k)\).

Geen coëfficiënt uit v7.6.22-amplitude. \(1/(8\pi)\) mag alleen bij onafhankelijke afleiding + freeze vóór runs + holdouts.

## Implementatie

1. Registry-bestand/constante met formule-id, afleidingsreferentie, freeze-datum.
2. Runner evalueert residual vs signed/directed observables.
3. Amplitude op continuum of N_max; nooit N=128-selectie + high-res convergence als PASS.
4. Changelog: dominantie ≠ SST-klokwet.

## Gates / acceptatie

- Alle preregister-velden aanwezig vóór eerste evaluatierun.
- HoldoutPass verplicht.
- Post-hoc add zonder afleiding → ENGINE/process FAIL.

## Tests

- Unit: registry weigert late insert zonder `derivedFrom`.
- Replay: bekende FAIL-kandidaten blijven FAIL.

## Versie

`7.6.31` (nieuw patchnummer; niet hergebruiken van eerdere roadmap-labels)

## Buiten scope

Confirmatoire v7.7.0-promotie (VL07); solverkoppeling.
