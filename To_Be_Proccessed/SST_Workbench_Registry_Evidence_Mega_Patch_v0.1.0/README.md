# SST Workbench Registry & Evidence Mega Patch v0.1.0

Purpose: repair the semantic split between reproducibility/migration status, execution status, and scientific verdicts in `SST-Workbench`, while preserving all historical scientific outputs and provenance.

This patch is designed to be handed to Cursor and executed from:

`C:\workspace\projects\SST-Workbench`

## Core changes

1. `FAMILY.yaml`:
   - migrate legacy `gate:` -> `repro_gate:`
   - preserve the old contents exactly as structured data
   - add explicit `execution:` and `scientific:` namespaces
   - normalize invalid/null version metadata such as A003 `version: -`

2. `falsifier_registry.yaml`:
   - archive the legacy registry unchanged
   - regenerate a new registry from the physical `01_research/A_falsifiers` tree
   - never use stars/emoji as canonical machine-readable evidence
   - distinguish `UNTESTED`, `INDETERMINATE`, `FALSIFIED_WITHIN_SCOPE`, `NOT_EVALUABLE`, etc.

3. Targeted scientific corrections:
   - A004 C9: record the existing C9 result as `FALSIFIED_WITHIN_SCOPE`, without converting post-hoc scaling into a new prediction
   - A023: separate RPO from Floquet; RPO is negative in the scanned regime where evidenced, Floquet is `NOT_EVALUABLE` when no valid RPO exists
   - A003: repair invalid YAML (`version: -` -> null)
   - A042: preserve current blind/reveal/provenance structure; no scientific verdict is invented by this patch

4. Consistency:
   - physical tree is authoritative for family existence
   - version directories are authoritative for on-disk versions
   - registry is regenerated from tree + explicit evidence overrides
   - missing A005 remains reserved/archival, not silently recreated
   - A043 remains occupied by Knot State Algebra if physically present
   - no new A-ID is allocated by this patch

5. Safety:
   - dry-run is the default
   - every changed file is backed up under `10_docs/migration/registry_evidence_patch_v0.1.0/backups/`
   - a JSON change ledger and SHA-256 manifest are emitted
   - scientific outputs/ZIPs are never modified

## Recommended execution

First:

`run_patch_dry_run.cmd`

Inspect:

`10_docs\migration\registry_evidence_patch_v0.1.0\DRY_RUN_REPORT.md`

Then, only if the report is correct:

`run_patch_apply.cmd`

Finally:

`run_validate.cmd`
