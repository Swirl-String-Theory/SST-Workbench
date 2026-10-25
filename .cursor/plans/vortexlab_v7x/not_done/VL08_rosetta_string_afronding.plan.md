---
name: VL08 rosetta string afronding
overview: Afronden van v7.6-S — classicalE2-alias, log-slider, runTheory, Rosetta-kaarten, radiusDrive-guardrails en Planck-invariantietest.
todos:
  - id: s1-rest
    content: "classicalE2 als alias van sstCore; log-slider over ~29 ordes"
    status: pending
  - id: s2-runtheory
    content: "runTheory He-II|SST|String/Rosetta + readoutkaarten a/ℓ_P, a/r_c, R/a, log10 a"
    status: pending
  - id: s3-radiusdrive
    content: "radiusDrive physical-only default + simulation expert + Biot–Savart-vloer"
    status: pending
  - id: planck-invariant-test
    content: "Nieuwe zelftest (niet T7 — T7=ghost) Planck-preset bit-identiek zolang radiusDrive≠simulation"
    status: pending
isProject: false
---

# VL08 — Rosetta / String-afronding (v7.6-S rest)

Parent: [VORTEXLAB_V7X_EPIC.plan.md](../complete/VORTEXLAB_V7X_EPIC.plan.md) · Parallel na: [VL00](VL00_baseline_reach.plan.md)

## Bron

- Stappenplan v4/v5 §4 items 12–15
- Stappenplan v6 §6 (aPhys al deels in productie)

## Status

**Spec + minimale hooks · UI/T14-volledig next.** Spec: [`docs/planning/VL08_rosetta_string_spec.md`](../../05_apps/A003_vortexlab/docs/planning/VL08_rosetta_string_spec.md). Aanwezig: `PLANCK_LENGTH`, He-core-ref, passieve `a_probe` / Planck-presets (v7.5.4, v7.6.24b), R_horn/r_kern/a_sim-scheiding (v7.5.1), Fluid-P2 `SUB_PRECISION_CORE`, `ROSETTA_DEFAULTS` in `research-track-vl.js`, minimale `P.radiusDrive` / `P.runTheory` / T14-hooks in runtime. Nog open: UI-seg/kaarten/confirm voor simulation-modus, log-slider ~29-ordes fine-tune, volledige T14 in browser-campagne.

## Wat bestaat al

- `parseLengthInput` / `fmtLengthSI` / SI am–m.
- String-probe medium + preset ℓ_P (metadata-only).
- Runtime-constanten L112–L113; a_probe stuurt nooit solver/BEM/contact.

## Doel

1. **S1-rest:** `classicalE2` expliciet als alias van `sstCore` (½r_e ≈ r_c is SST-identificatie, geen tweede ijkpunt); log-slider over ~29 ordes.
2. **S2:** `runTheory` ∈ {He-II, SST, String/Rosetta}; kaarten a/ℓ_P, a/r_c, R/a, log₁₀a; tension-proxy alleen readout; α_ring-naamgevingsfirewall.
3. **S3+S7:** `radiusDrive` `'physical-only'` default | `'simulation'` expert met waarschuwing; numerieke Biot–Savart-vloer.
4. **Invariantietest:** Planck-preset activeert → filamentdynamica bit-identiek zolang `radiusDrive ≠ 'simulation'`. **Nieuw T-nummer** (T7 is ghost-test).

## Implementatie

1. UI-schakelaars + ModelLog-velden.
2. Predicaten: physical-only blokkeert a_probe → a_sim mutatie.
3. Zelftest naast T0j/T11–T13.
4. Docs: bewuste planafwijking sinds v7.3 (a&lt;1 µm open) wordt door radiusDrive gesloten.

## Gates / acceptatie

- Default start: radiusDrive=physical-only; Planck-preset wijzigt velocityCore-hash niet.
- Simulation-modus logt waarschuwing + vereist expliciete bevestiging.
- Geen energieclaim op tension-proxy.

## Tests

- Node: hash Y-traject met/zonder Planck-preset.
- UI-selftest markers.
- `npm run check`

## Versie

Patch op 7.6.x-lijn of `7.6.S1` — kiezen bij implementatie; geen solverkoppeling van Rosetta naar klokwet.

## Buiten scope

ξ↔r_kern documentgate (VL09); continuum (VL13).
