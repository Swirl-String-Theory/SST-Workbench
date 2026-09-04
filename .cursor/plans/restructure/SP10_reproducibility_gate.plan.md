---
name: SP10 reproducibility gate
todos:
  - id: t00
    content: "Gate every active family's `latest` (install → build → run → manifest)"
    status: pending
  - id: t01
    content: "Record tolerances in `FAMILY.yaml` gate section"
    status: pending
  - id: t02
    content: "Write `reproducibility_gate.md`"
    status: pending
  - id: t03
    content: "Special cases: blind-only, datasets, non-runnable, GPU skip-with-reason"
    status: pending
  - id: t04
    content: "Done-criteria: no unjustified fails; gate report committed"
    status: pending
---
# SP10 — Reproducibility gate

Status: `PLANNED` · Priority: P3 · Risk: medium · Depends on: SP09

## Todos

Progress tracker — checkboxes include completed work so status is obvious at a glance.

- [ ] Gate every active family's `latest` (install → build → run → manifest)
- [ ] Record tolerances in `FAMILY.yaml` gate section
- [ ] Write `reproducibility_gate.md`
- [ ] Special cases: blind-only, datasets, non-runnable, GPU skip-with-reason
- [ ] Done-criteria: no unjustified fails; gate report committed

**Next:** Blocked on SP09

The gate that decides whether the migration succeeded. Nothing is deleted until this passes.

The standard is **not** "imports work". It is:

```text
old version + old dataset
        |
        v
scientifically equivalent result
        |
        v
from the new filesystem location
```

A falsifier that imports cleanly, runs to completion, and returns a different number than it did
before the move has failed this gate. That failure mode is entirely plausible here: the datasets
moved, the resolver changed, and several packs had multiple competing path conventions that could
each have resolved to a different file.

## Scope

Every family with `status: active` in its `FAMILY.yaml`. Dormant, superseded and archived families
are exempt and the exemption is recorded, with the reason, in the gate report.

For each in-scope family, only its `latest` version is gated. Older versions are checked for
structural integrity (SP05's `test_no_orphan_versions.py`) but not re-run — re-running 275 versions
is not proportionate, and the older ones are preserved precisely so they *can* be re-run when a
specific question arises.

## Per-family sequence

```text
install
  -> build native backend
    -> basic run
      -> extended run, where practical
        -> output manifest
          -> SHA-256
```

Concretely:

1. `run_01_install.cmd` or equivalent, into a clean environment.
2. Build the native backend. Many families have `cpp/` and a `build_ext_if_needed.py`; several of
   those use `parents[3]`, which changed depth. This step catches resolver gaps that a pure-Python
   import test misses.
3. Basic run, from the new location, against the dataset resolved through `SST_KNOT_DATASET`.
4. Extended run where runtime allows. Record which families were basic-only and why.
5. Produce the output manifest and hash it.

## Comparison baseline

Three tiers, in descending order of strength. Use the strongest available per family.

**Tier 1 — archived pre-migration run.** If `Restore_Archives/` or a `*_outputs.zip` holds a run of
the same version against the same dataset, compare against it directly. 607 zips are available;
many families have one.

**Tier 2 — pre-move run captured during SP05.** The pilot (A037) established this pattern.
Where a family was re-run before its move, that manifest is the baseline.

**Tier 3 — old-path run captured now.** Run the family through its old junction path and through
its new path, and compare the two. Weaker, because both paths resolve through the same current
code, but it still catches dataset resolution errors — which are the dominant risk.

Record which tier each family used. A family gated only at Tier 3 is a known weaker result, not a
pass to be treated as equivalent to Tier 1.

## Numerical equivalence, not byte equality

Byte-identical output is the ideal but not the criterion. Legitimate sources of difference:

- Timestamps and run IDs embedded in manifests.
- Absolute paths recorded in provenance blocks — these *should* differ, and a manifest that records
  the old path after the move is itself a finding.
- Non-deterministic thread scheduling in OpenMP or SYCL backends.

The criterion is that every **scientific quantity** in the manifest matches to the family's own
declared tolerance. Where a family declares no tolerance, use exact equality for integers and
topological invariants, and a documented relative tolerance for floating-point scalars.

`FAMILY.yaml` gains a `gate` block recording what was compared and to what tolerance, so the
judgement is inspectable rather than implicit.

## Special cases

**Blind families.** Run the blind path only. Do not unblind to check a number — that destroys the
blinding for any future use of that version. Compare blind-stage outputs.

**Families whose dataset also moved.** A001 (`knotplot_relaxed`) moved in SP07 and is the default
input for 40+ packs. For every family consuming it, verify the resolved dataset directory has the
same file count and the same aggregate hash as before the move, before attributing any numerical
difference to the pack.

**Families with no runnable entry point.** `SST_derive_constants_research` (manuscripts and gate
scripts), `SST_timefield_spectral_v06_research` (output-only). These are gated structurally: every
referenced file resolves, no path is dead. Record them as structurally gated.

**GPU and SYCL families.** `06_templates/SST_GPU_SYCL_DPC_audit_template` and any family using the
SYCL backend may not run on every machine. Record as skipped with the hardware reason rather than
marking pass.

## Gate report

`10_docs/migration/reproducibility_gate.md`, one row per in-scope family:

```text
catalog_id, version, tier, native_build, basic_run, extended_run, equivalence, tolerance, note
```

Status values: `pass`, `fail`, `skipped`, `structural`. Anything that is not `pass` needs a written
reason.

## Tests to write

- `test_gate_coverage.py` — every family with `status: active` appears in the gate report; every
  non-`pass` row has a non-empty reason.
- `test_dataset_integrity.py` — for each dataset in `03_data/A_knots/`, file count and aggregate
  hash match `checksums.sha256` from SP00.
- `test_manifest_compare.py` — the comparison harness itself: given two manifests, it correctly
  ignores timestamps and paths while catching a changed scientific quantity. Test it with a
  deliberately altered manifest, or it will pass everything.

## Rollback

Nothing to roll back. A failing gate blocks SP11; it does not revert SP04–SP09. Diagnose the
specific family, fix the resolver or the path, re-run. The junction layer is still in place
throughout, so a family that fails the gate can be run through its old path while being fixed.

## Done criteria

- Every `status: active` family has a gate row.
- No `fail` rows remain, or each remaining one has an accepted written justification.
- At least ten families gated at Tier 1 or Tier 2, so the result does not rest entirely on the
  weaker Tier 3 comparison.
- Dataset integrity confirmed for every dataset that moved.
- The gate report is committed. It is the evidence that the restructure preserved the science.
