# Pilot preflight validation - 2026-10-26

Actual commands run from the repository root:

* `python -m unittest discover -s 07_scripts/sst_migration -p test_preflight.py -v`
  - Exit 0; three tests pass (exclusive lock, manifest traversal rejection,
    one job per call with blocked inputs and no science promotion/source writes).
* `python 07_scripts/sst_migration/preflight.py init --state 10_docs/migration_v110/pilot_20261026`
  - Exit 0; 75 families, 297 direct disk versions; framework source audit blocked.
* `python 07_scripts/sst_migration/preflight.py preflight-next --state 10_docs/migration_v110/pilot_20261026`
  - Three sequential invocations, each exit 0 for a successfully recorded preflight:
    A011, A054, A065. Exit 0 here does NOT mean migration or science passed.
* `python 07_scripts/sst_migration/preflight.py status --state 10_docs/migration_v110/pilot_20261026`
  - Exit 0; 3 BLOCKED_PREFLIGHT, 72 WAITING_PILOT; scheduling_enabled=false,
    pilot_validated=false.
* `render_reports.py --state 10_docs/migration_v110/pilot_20261026`
  - Bundled Python/reportlab runtime, exit 0; three one-page PDFs generated.
* Poppler rendered all three pages; all were visually inspected. No clipping or
  overlap observed. Poppler emits local font-map warnings about unused font names;
  rendering completed successfully. pypdf reopened every report and found one page.
* `git diff --check -- 07_scripts/sst_migration 10_docs/migration_v110`
  - Exit 0. New files are untracked, so this command alone is not a diff review;
    the added source, documentation, queue/results and rendered reports were also
    inspected directly. No commit or push was performed.

`pilot_20261026/ARTIFACT_SHA256.json` hashes inventory, source audit, queue,
per-run JSON, PDFs and preview images. It does not claim to seal scientific data.

Not executed: framework regression/native/backend tests, actual family migration,
new-version creation, freeze/reveal, falsifier numerical smoke, full campaign,
carrier payload hash verification, physical qualification, Scheduled account access
test or automatic scheduling. Per-family adapters are not implemented in this tranche.

Next prerequisite: resolve the framework byte mismatch from authentic sealed source,
reconcile pilot registry identities, and establish admitted dataset/provider payloads
and per-family contracts. Preserve this snapshot; use a fresh evidence directory
for any corrected preflight.
