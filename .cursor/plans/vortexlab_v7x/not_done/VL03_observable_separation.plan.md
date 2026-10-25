---
name: VL03 observable separation
overview: Hernoem legacy proxyvelden en splits CLOCK-UI in vier semantische blokken (roadmap v7.6.28).
todos:
  - id: rename-fields
    content: "phaseLogRatio→rigidResponseLogRatio; omegaBody→omegaRigidCenterline; fieldLogMin/Max→kinematicClockEnvelopeMin/Max; v_def→centerlineDeformationResidual"
    status: pending
  - id: ui-blocks
    content: "UI-blokken KINEMATIC CLOCK / RIGID CARRIER RESPONSE / GEOMETRIC THICKNESS / INTERNAL PHASE — NOT YET RESOLVED"
    status: pending
  - id: schema-bump
    content: Schema-bump zonder compatibiliteitsalias (precedent v7.6.20)
    status: pending
isProject: false
---

# VL03 — Observable-separation cleanup (v7.6.28)

Parent: [VORTEXLAB_V7X_EPIC.plan.md](../complete/VORTEXLAB_V7X_EPIC.plan.md) · Blokkeert op: [VL02](VL02_afstand_orientatie_multipool.plan.md)

## Bron

- Roadmap §v7.6.28
- Analyse v7.6.22 §12 v7.6.27

## Status

**Open.** Runtime bevat nog `phaseLogRatio` (~30×), `omegaBody`, `fieldLogMin`/`fieldLogMax`; geen vier UI-bloklabels.

## Wat bestaat al

- Canonieke `v↺*`-notatie (v7.6.20).
- R15 gelabeld als scale-screen, geen closure (v7.6.23).
- Intrinsieke Ω naast legacy lab-z (v7.6.24).

## Doel

Hernoemingen:

| Oud | Nieuw |
|-----|-------|
| `phaseLogRatio` | `rigidResponseLogRatio` |
| `omegaBody` | `omegaRigidCenterline` |
| `fieldLogMin` / `fieldLogMax` | `kinematicClockEnvelopeMin` / `Max` |
| `v_def` | `centerlineDeformationResidual` |

UI-blokken: (1) KINEMATIC CLOCK (2) RIGID CARRIER RESPONSE (3) GEOMETRIC THICKNESS (4) INTERNAL PHASE — NOT YET RESOLVED.

## Implementatie

1. Globale rename in runtime, exports, gates, docs.
2. Geen alias-keys in nieuw schema (historische exports blijven historisch).
3. Dom-secties + CSS; INTERNAL PHASE blijft leeg tot VL04+.
4. Selftest eist nieuwe keys en verbiedt oude in verse exports.

## Gates / acceptatie

- Verse JSON bevat uitsluitend nieuwe keys.
- D1-tekst verwijst naar `centerlineDeformationResidual`.
- UI toont vier blokken; blok 4 expliciet unresolved.

## Tests

- `rg` op oude keys in `apps/web` → 0 in actieve code (archief uitgezonderd).
- Selftest schema-suffix.
- `npm run check`

## Versie

`7.6.28`

## Buiten scope

Bishop-frame inhoud (VL04); fysica van dikte/reach (VL00).
