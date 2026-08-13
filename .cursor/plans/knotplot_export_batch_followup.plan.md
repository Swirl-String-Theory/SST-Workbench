---
name: KnotPlot export batch
overview: "Vervolg op fseries batch: KnotPlot knots/tori/links exporteren + relaxen, daarna --all-knotplot in run_catalog_batch met dezelfde resolutieladder."
todos:
  - id: inventory-missing
    content: Inventariseer welke knot_/torus_/link_ folders nog geen trial TXT / settled seed hebben
    status: pending
  - id: export-relax-campaign
    content: Batch export + KnotPlot relax (run_build zonder/met -rr) tot gated trial seeds bestaan
    status: pending
  - id: batch-all-knotplot
    content: "Extend run_catalog_batch met --all-knotplot / --kind knot,torus,link; hergebruik 150..1200 ladder"
    status: pending
  - id: tests-docs
    content: Unit tests discovery/flags; README; baseline+after unittest suite
    status: pending
dependsOn: fseries_batch_ladder_94660855
isProject: false
---

# Vervolg: KnotPlot export/relax + batch

**Depends on:** [fseries_batch_ladder_94660855](fseries_batch_ladder_94660855.plan.md) (phase 1 fseries batch + variable base N).

## Goal

Veel KnotPlot knots, tori en links zijn nog **niet geëxporteerd / relaxed**. Dit plan:

1. Inventariseert en vult ontbrekende `knots/knot_*`, `torus_*`, `link_*` trial outputs.
2. Voegt `--all-knotplot` (en `--kind`) toe aan `run_catalog_batch`, dezelfde ladder als fseries: `-r150,300,600,900,1200 -t12`.

## Approach

- Inventory script of dry-run: folders zonder `*_trial_*.txt` / zonder bruikbare gate-seed.
- Per id: bestaande `run_build.cmd <id>` → relax → optioneel `-rr` seed gate; **geen** breaking change aan `run_build.cmd` defaults.
- Batch discovery: `run_catalog_knot` KnotPlot mode (`--knot3.1`, `--go 1k`, …) in een lus; skip ids zonder seed met duidelijke summary-status `missing-seed`.
- Outdir blijft `out/K3.1/g1k/t12/` (bestaande conventie).

## Out of scope hier

- Fseries-only batch (phase 1)
- VortexLab/catalog upsert (eigen vervolgplan)
- Parallel knot workers (eigen vervolgplan)

## Verification

- Unit tests voor discovery + skip-missing
- Dry-run lijst van available vs missing
- Smoke één knot + één torus of link na export
