---
name: Batch parallel knots
overview: "Vervolg: parallel meerdere knopen tegelijk in run_catalog_batch, met resource caps en veilige outdirs (na sequential fseries batch)."
todos:
  - id: worker-pool
    content: "Add --jobs N worker pool in run_catalog_batch (process-level); default blijft 1"
    status: pending
  - id: resource-caps
    content: Cap jobs vs --threads (bijv. jobs*threads CPU-aware); documenteer Windows I/O/disk tips
    status: pending
  - id: summary-locking
    content: Thread/process-safe batch summary + per-stem logs zonder overlap
    status: pending
  - id: tests
    content: Unit tests voor scheduling, fail-fast, summary merge; full suite before/after
    status: pending
dependsOn: fseries_batch_ladder_94660855
isProject: false
---

# Vervolg: parallel multi-knot batch

**Depends on:** [fseries_batch_ladder_94660855](fseries_batch_ladder_94660855.plan.md).

## Goal

Phase 1 draait knopen **sequentieel**. Dit plan voegt `--jobs N` toe zodat meerdere stems tegelijk RR draaien, zonder outdir-collisions.

## Approach

- Process pool (niet threads): elk child runt één `run_catalog_knot` pipeline.
- Default `--jobs 1` (huidig gedrag).
- Cap: waarschuw/clamp als `jobs * threads` > logische CPUs (bij `-t12` typisch `jobs=1` of `2`).
- Per-stem outdir al geïsoleerd (`out/<stem>/t12/`); summary via atomic write of merge aan einde.
- `--fail-fast` stopt queue + cancelt pending; running children krijgen nette terminate waar mogelijk.

## Verification

- Unit tests met gemockte per-stem runner
- Smoke `--jobs 2 --stems 3_1,4_1 -r150` (kort) alleen na suite groen
