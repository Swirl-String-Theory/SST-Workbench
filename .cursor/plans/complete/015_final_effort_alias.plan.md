---
name: final effort alias
overview: "Additieve final-snapshots in ridgerunner/: KnotPlot naast .kpc; out-campaigns onder out/. Inclusief run_finalize_knotplot.cmd die knots/ scant. RR-pipe ongewijzigd."
todos:
  - id: write-final-snapshot
    content: "ridgerunner/write_final_snapshot.py (+.cmd): --suffix, dest rules, best across tN"
    status: completed
  - id: run-finalize-knotplot
    content: "run_finalize_knotplot.cmd/.py: scan KnotPlot/knots, write build_*_final_* next to each kpc"
    status: completed
  - id: wire-outer-only
    content: Optional auto-wire outer drivers after success; snapshot fail = warning
    status: completed
  - id: tests-docs
    content: Unit tests + README for finalize scanner and snapshot CLI
    status: completed
isProject: false
---

# Final snapshots + run_finalize_knotplot

## In `KnotPlot/ridgerunner/`

- `write_final_snapshot.py` / `.cmd` — shared copy helper (`--suffix`, `--from-outdir`, `--dest`)
- **`run_finalize_knotplot.cmd`** — scans `../knots`, finds polish + `build_*.kpc`, writes `build_*_final_{tag}_{ts}.txt` **next to the kpc**

```bat
cd KnotPlot\ridgerunner
run_finalize_knotplot.cmd
run_finalize_knotplot.cmd --kind knot --suffix backlog --dry-run
```

## Destinations

- KnotPlot: `knots/knot_3.1/build_knot_3.1_final_….txt`
- fseries/ideal: `out/<campaign>/` best over `tN`

## Constraints

RR pipe untouched; additive only; post-hoc without full re-run; no overwrite.
