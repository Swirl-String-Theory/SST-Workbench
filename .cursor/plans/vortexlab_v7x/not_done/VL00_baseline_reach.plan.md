---
name: VL00 baseline reach
overview: Vastleggen van de huidige reach/DCSD-acceptatie en versiestringconsistentie op runtime 7.6.25b voordat Research Track v7.6.26+ start.
todos:
  - id: version-align
    content: package.json / APP_VERSION / footer / title op één string zetten
    status: pending
  - id: browser-selftest
    content: "?selftest=1 groen inclusief reach-kernel T0e25a"
    status: pending
  - id: reach-standard-run
    content: Continue reach/DCSD Standaard op 3_1–6_1 Ideal+Fseries; R22/G4/G5 vastleggen
    status: pending
isProject: false
---

# VL00 — Baseline reach en versiestring

Parent: [VORTEXLAB_V7X_EPIC.plan.md](../complete/VORTEXLAB_V7X_EPIC.plan.md)

## Bron

- Analyse v7.6.22 §9 + §12 v7.6.24 (reach/DCSD-acceptatie)
- Roadmap v7.6.25–v7.7.0 §v7.6.25 (geïmplementeerd; acceptatie open)
- Changelog `vortexring-lab-v7.6.25b-changelog.md`

## Status

**Deels gedaan.** Continue DCSD/reach-solver staat in v7.6.25/25a/25b (G0–G5, G4a/b, R41, R42). `npm run check` PASS bij epic-aanmaak. Interactieve browser-reach-run en formele diameterfout &lt;0.5% zijn niet vastgelegd. Versiestrings divergeren.

## Wat bestaat al

- Runtime: continue curvature / DCSD / inter-component reach; legacy `approximateDoublyCriticalDistance` blijft diagnostiek.
- Workflowstap na continuum: Continue reach/DCSD (Quick / Standaard / Confirmatory).
- Schema export: `vortexlab-continuous-reach-audit/1.0`.
- `APP_VERSION='7.6.25b-m1-fluidqual-p2'` in `apps/web/src/legacy/vortexlab-runtime.js`.
- `package.json` version: `7.6.25-m1-fluidqual-p2` (mist `b`).

## Doel

1. Eén canonieke versiestring over package, runtime, title, footer, ModelLog.
2. Browser-zelftest groen.
3. Standaard-reach-run op unknot-anker + Ideal/Fseries `3_1`…`6_1` met vastgelegde G4/G5/R22-status (PASS of eerlijke FAIL met JSON).

## Implementatie

1. Versie-alignment (patch, geen fysica).
2. `npm start` → `?selftest=1`.
3. CLOCK-workflow: SPEC → decompositie → holdouts → continuum → **Continue reach/DCSD · Standaard**.
4. Export JSON/TXT archiveren onder `validation/` of session-export; status in dit subplan bijwerken.

## Gates / acceptatie

- Diameter/reachfout vs metadata &lt;0.5% en niet systematisch groeiend met N (originele acceptatie), **of** expliciete RESEARCH FAIL met limiter-provenance.
- G0–G5 niet vacuüm PASS (G4a blijft afdwingen).
- R42 blijft INFO voor KnotPlot D=1 vs discrete proxy.

## Tests

- `npm run check`
- Browser `?selftest=1`
- Reach Standaard-export handmatig geïnspecteerd

## Versie

Patch op 7.6.25b-lijn (bijv. `7.6.25b-m1-…` of `7.6.25c` alleen als acceptatie wetenschappelijk wijzigt).

## Buiten scope

Signed route (VL01), nieuwe κ-factoren, solverkoppeling van continuous reach naar `a_sim`.
