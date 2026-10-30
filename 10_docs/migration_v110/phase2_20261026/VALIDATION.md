# Phase 2 validation - 2026-10-26

Scope: integrity, catalog reconciliation, admission contracts and bounded software
checks. No full scientific campaign, successor release, freeze or reveal was run.

## Executed checks

All commands ran from `C:\workspace\projects\SST-Workbench`.

* `python -B 07_scripts/sst_migration/phase2_integrity.py framework --out 10_docs/migration_v110/phase2_20261026`
  - Exit 0. RC2 ZIP SHA-256 exactly equals the existing canonical freeze digest.
    All 110 RC2 manifest entries match. The installed DD32 document differs only
    in Markdown math delimiters and EOF newline. Both byte hashes and copies and
    a unified diff are retained. Installed bytes remain mismatched, not repaired.
* The canonical frozen distribution was independently opened and all its 112
  PACKAGE_MANIFEST entries verified, with no mismatch. The original DD32 document
  digest matches the RC2 document. `canonical_distribution_integrity.json` records
  the distribution SHA-256 and count.
* `phase2_integrity.py geometry --out ...`, using the bundled Python/numpy runtime
  - Exit 0. All 2,227 topology directories inspected; 4,497 carrier descriptor
    records checked. Every raw source SHA-256 and source-native geometry digest
    matches. All returned coordinate arrays are finite. 2,312 records belong to
    the active multiseed view. A second byte pass verified all 2,282 distinct raw
    source files unchanged at the end. No solver or metric convergence campaign.
* `phase2_integrity.py seals --out ...`
  - Exit 0. A065 D01/D02/D03 exact file sets, seven payload hashes, all self-hashes
    and global commitment bindings match. No private targets opened. All 11
    inherited source manifests were compared with the current tree; differences
    in older historical manifests are contextual, not treated as new corruption.
    The current v0.4.3 source manifest has three byte mismatches, investigated next.
* `phase2_integrity.py pilot_archives --out ...`
  - Exit 0. Local Downloads A054-v0.5.1 and A065-v0.4.3 source ZIPs have respectively
    59/59 and 159/159 matching internal entries. Their origin is local Downloads;
    no independent trusted ZIP signature/digest was claimed. All local differences
    were copied and diffed. Normalized comparison: four Markdown files differ only
    by math delimiters/EOF; A065 report_tex.py differs only by CRLF/LF. Existing
    research source files and historical manifests were not changed.
* `python -B 07_scripts/sst_migration/phase2_registry.py`
  - Exit 0 after correcting handling of existing A050 version entries without an
    explicit directory. Only this operation's partial metadata edits were resumed
    from the saved baseline. Final result: 25 created and 7 updated FAMILY files;
    73 canonical A identities in both indices. Every existing changed metadata file
    has an exact pre-edit backup. Two noncanonical locations remain preserved.
    Other index domains and non-A research groups pass structural equality checks.
* `python -B 07_scripts/sst_migration/phase2_admission.py`
  - Exit 0. Three explicit JSON contracts generated. A011: 1,924 geometry-diagnostic
    candidates admitted and 388 excluded, with per-carrier reasons. These capability
    predicates are a proposal for a future successor, not edits to old science gates.
    A054: all 47 E011 anchors and 13 historical E013 manifests pass current hashes,
    exact source-locator joins and self-hash checks. Exactly one A054 contract enabled.
    L2a1 has one provider even in FULL/CERTIFY; other selected knots have two there.
* `py -3.14 -B 07_scripts/sst_migration/phase2_a011_check.py`
  - Actual executable: Python 3.14.3 at the installed pythoncore-3.14-64 location.
    Exit 0; 4 tests pass. Existing native `_native.cp314-win_amd64.pyd`, C++17
    backend 0.3.1, imported directly without the historical package auto-builder.
    Three geometry tests plus native/reference velocity, writhe and distance parity.
    See `a011_geometry_parity.log`.
* A054 pytest: `test_e013_manifest.py`, `test_contract.py`, `test_commitment.py`
  - Python 3.14.3, `-B -p no:cacheprovider`, temp files under this evidence directory.
    Exit 0; 6 tests pass. See `a054_contract_tests.log`.
* A065 pytest: three selected checks in `test_v039_a003_framework.py`
  - Precommit locked, framework gate graph, and framework version pin. Python
    3.14.3, `-B -p no:cacheprovider`; exit 0; 3 passed, 4 deselected.
    See `a065_framework_static_tests.log`. No volume/filament/FFT run.
* `python -B -m unittest discover -s 07_scripts/sst_migration -p 'test_*.py' -v`
  - Exit 0; 8 tests pass, including existing exclusive lock/single-item checks and
    new assertions on the full evidence, unchanged other catalog domains, seals,
    contracts, disabled queue and absence of proposed successor directories.
    See `queue_evidence_tests.log`.
* Existing `07_scripts/test_build_family_hierarchy.py`
  - Python 3.14 pytest, isolated temp directory, cache disabled; exit 0; 4 tests pass.
  - Total distinct targeted tests across these groups: 25 passed.
* `python -B 07_scripts/sst_migration/phase2_finalize.py`
  - Exit 0. Phase 1 artifact snapshot verified before mutable queue update. Exact
    previous queue retained as `queue.before_phase2.json`. Three pilots retain
    migration BLOCKED, migrated execution NOT_RUN and science NOT_RUN. No scheduling.
* `render_phase2_report.py` using bundled Python/reportlab
  - Exit 0. Seven-page PDF generated from fixed JSON evidence. pypdf reopened it;
    Poppler rendered all seven pages and each was visually inspected. No clipping,
    broken glyphs or overlaps observed. Local unused-font mapping warnings are
    captured in `poppler_render.log`; rendering completed with exit 0.
* Final preservation audit: all 713 Phase 1 version-metadata pins still match;
  all 14 Phase 1 artifact entries match when the mutable queue is checked against
  its exact saved pre-update snapshot. See `preservation_final.json`.
* Final scoped `git diff --check`: exit 0. The seven existing FAMILY edits, both
  registry updates, new FAMILY records, source helpers and evidence were inspected.
  Git emits ordinary LF-to-CRLF checkout notices, not validation failures.

## Evidence and limitations

`gate_overview.json` is the decision ledger. `required_patches.json` and
`REQUIRED_PATCHES.md` identify nine remaining source/admission/adapter/data/production
items, stages and acceptance criteria. Open nonpilot latest pointers and ambiguous
suffix/work/report directories remain explicit; no canonical selection was inferred
from version number alone. There are 25 open latest pointers including the preexisting
unversioned A003, and seven affected ambiguous-directory groups.

The old Phase 1 `ARTIFACT_SHA256.json` remains unchanged. Its historical queue digest
now intentionally refers to the exact saved `queue.before_phase2.json`, not to the
updated mutable queue. Other historical Phase 1 evidence still matches its old hash.
New Phase 2 artifact hashes include the updated queue and reconciled metadata.

Source authority, byte integrity, dataset capability, implementation checks and
physical certification remain separate. Scientific certification and migrated
execution were NOT_RUN. The existing source-tree unit checks do not qualify a new
version. No source-data, historical raw result, original seal, commitment or source
manifest was rewritten to make a gate pass. No commit, push or scheduling change.
