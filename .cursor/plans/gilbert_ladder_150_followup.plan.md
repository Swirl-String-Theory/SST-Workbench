---
name: Gilbert ladder 150
overview: "Vervolg: Gilbert run_ideal_knot default/optie voor base N=150 en ladder 150,300,600,900,1200 — zonder phase-1 default te breken."
todos:
  - id: ideal-base-flag
    content: "run_ideal_knot --resolutions 150,300,600,900,1200 werkt via gedeelde variable-base helpers uit phase 1"
    status: pending
  - id: default-policy
    content: "Besluit documenteren: default blijft 300,300+ of opt-in -r150,...; target L_3_1 compare per rung"
    status: pending
  - id: tests-docs
    content: Unit tests ideal path base=150; README; suite before/after
    status: pending
dependsOn: fseries_batch_ladder_94660855
isProject: false
---

# Vervolg: Gilbert default / 150 ladder

**Depends on:** [fseries_batch_ladder_94660855](fseries_batch_ladder_94660855.plan.md) (variable base helpers).

## Goal

Phase 1 laat Gilbert/`run_ideal_knot` default op **N=300** staan. Dit plan maakt de fseries-ladder (`150,300,600,900,1200`) beschikbaar en documenteert default-policy voor ideal AB runs (target `L_3_1 = 16.357467488` per polish).

## Approach

- Geen breaking change: CLI default blijft `300,600,1200` tenzij expliciet `-r150,300,600,900,1200`.
- Sample Gilbert AB op `min(resolutions)` vertices; rest via ladder upsample (zelfde als catalog).
- Compare helpers blijven diameter-conventie rapporteren per rung.

## Verification

- Unit tests parse/paths voor ideal base 150
- Smoke `--3:1:1 -r150,300` optioneel na suite
