# Cursor task: SST Workbench Registry/Evidence repair

Work in the repository root:

`C:\workspace\projects\SST-Workbench`

You are applying the supplied `SST_Workbench_Registry_Evidence_Mega_Patch_v0.1.0`.

## Non-negotiable rules

- Do not delete or rewrite scientific output ZIPs, raw outputs, blind archives, reveal archives, or historical version directories.
- Do not alter any numerical result to make it fit a theory.
- Do not reinterpret a migration/reproducibility PASS as a physics PASS.
- Do not invent a scientific verdict where the evidence is absent.
- Do not allocate a new catalog ID.
- Preserve A043 if it already exists physically.
- Keep A005 reserved/archive-only unless a verified original package is recovered.
- Keep BLIND and REVEAL/PRIVATE material separated.
- All changes must be reversible.

## Goal

Refactor repository metadata so that these are separate concepts:

1. `repro_gate` — migration/reproducibility/equivalence status
2. `execution` — whether tests/runs completed
3. `scientific` — hypothesis/claim verdict and scope
4. `provenance` — preregistration, blinding and source-independence status

The old `gate:` block in `FAMILY.yaml` is a migration/repro gate. Rename/migrate it to `repro_gate:`.

## Known corrections to preserve

### A003
`FAMILY.yaml` currently contains invalid YAML equivalent to:

`version: -`

Change only the null semantics:

`version: null`

Do not invent a version.

### A004 C9

The existing v0.4.0 C9 documentation defines:

`Q_Gamma = 2 ΔΩ_dyn / (Γ/A)`

with preregistered test:

`|Q_Gamma - 1| < 0.02`

The existing validation states that the hole-contained tests violate this threshold and concludes that bundle-average `Γ/A` is not sufficient to determine the observed trefoil clock rate within the frozen straight axial-bundle model.

Record this as:

- claim id: `C9_iso_gamma_area_dynamic_clock`
- verdict: `FALSIFIED_WITHIN_SCOPE`
- scope: `frozen_straight_axial_bundle_model`
- preregistration quality: `PARTIAL`
- reason: the C9 thresholds exist in `docs/08_iso_gamma_area_dynamic_clock.md`, while `docs/PREREGISTRATION.md` is not a dedicated frozen C9 preregistration artifact

Do NOT promote the post-hoc `Q/rr^2` scaling into a prediction.

### A023

Do not summarize the whole family as a physics PASS.

Represent the dependent gates separately:

- `RPO_recurrence`: `NEGATIVE_IN_SCANNED_REGIME` when the existing gate conclusions state that no valid excursion-and-return RPO candidate was found
- `Floquet_bounded`: `NOT_EVALUABLE` when Floquet was not evaluated because no valid RPO existed

Overall family scientific status may remain `INDETERMINATE` because the family contains multiple gates and regimes.

### A042

Do not invent a new verdict. Preserve all existing blind/reveal/provenance metadata. If `PROVENANCE_AUDIT.md` or a verdict file explicitly states a status, the registry builder may quote that status as source-derived metadata, but must not simplify it to a stronger claim.

## Required steps

1. Run `scripts\mega_patch.py --repo . --dry-run`
2. Review the generated report.
3. Fix only errors reported as blocking.
4. Re-run dry-run until clean.
5. Run `scripts\mega_patch.py --repo . --apply`
6. Run `scripts\validate_registry_v2.py --repo .`
7. Run existing repository tests that are cheap and relevant to metadata parsing.
8. Do not run multi-hour physics campaigns merely for this metadata patch.
9. Produce a final summary containing:
   - files changed
   - backups created
   - families discovered
   - versions discovered
   - legacy registry entries preserved
   - A-IDs missing from the physical tree
   - scientific overrides applied
   - validation failures, if any

## Acceptance criteria

- every `01_research/A_falsifiers/A*/FAMILY.yaml` parses as YAML
- no canonical `FAMILY.yaml` contains top-level `gate:`
- existing legacy gate data is present under `repro_gate:`
- A003 parses and has `repro_gate.version: null`
- A004 has an explicit C9 claim with scoped falsification
- A023 distinguishes RPO from Floquet and does not call unavailable Floquet a PASS
- generated registry includes every physical A-family
- registry does not claim physics PASS merely because `repro_gate.status == pass`
- generated registry contains no star/emoji rating as canonical evidence
- all modified source metadata files have backups and SHA-256 entries
