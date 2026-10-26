# Framework v1.0.10 migration pipeline: pilot preflight

Inspection date: 2026-10-26 (Europe/Amsterdam).

## Current delivery and decision

Implemented: reproducible registry/disk inventory, source-manifest audit, a persistent
exclusive-lock queue, one pilot preflight per invocation, immutable per-run JSON and
PDF preflight reports. This is a preflight foundation, not an operational scientific
migration worker. No falsifier version was created, migrated, executed, or certified.
Scheduling is disabled. The pilot is not validated.

The requested architecture-first gate found source drift and unresolved scientific
input admission. Creating apparent migrated successors before resolving these would
produce unqualified releases. Proposed versions below are reservations in a queue,
not registered releases. No existing source, result, manifest, or registry was changed.

## Authoritative sources and inventory

The live sources are `10_docs/registry/family_hierarchy.json` and
`10_docs/registry/catalog_index.json`; root-level copies do not exist. The hierarchy
is stamped 2026-09-29. Its A section contains 46 families. The union of both indices
and direct `01_research/A_falsifiers/A[0-9][0-9][0-9]_*` directories contains 75
families and 297 direct version directories. Embedded FRAMEWORK_INSTANCE directories,
runs, ZIP contents and output snapshots are not counted as releases.

`pilot_20261026/inventory.json` contains every family, all direct versions, declared
versions from each index, FAMILY latest and hash, selected package metadata hashes,
and discrepancies. `INVENTORY.md` is the readable companion. Directory presence is
not a scientific or release-quality verdict. Conflict/revision names remain visible;
they are not silently selected as latest. There are 30 families absent from at least
one index, 27 missing FAMILY.yaml files, and five hierarchy plus five catalog version
discrepancies. These require explicit reconciliation with authoritative metadata
before affected releases can be promoted. Do not regenerate indices from disk alone.

## Framework integrity

Canonical path: `06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.10`.
RELEASE_INFO and CANONICAL_FREEZE report RC2, CANONICAL_FROZEN. Historical validation
records 83 regressions and Windows/Arc A770 backend checks; those checks were not rerun
here. The freeze discloses overlay installation and no full Euler/PKLSA certification.

Current byte verification checked all 112 PACKAGE_MANIFEST entries. One differs:

* `docs/DD32_FP32X2.md`
* Expected SHA-256: `5929e8281569b049de50b17b6b40f8ae220f7891e4d5270740ab92a70fbd5579`
* Actual SHA-256: `a1ba867c3ddfa9cd61d72d6a3eb3aa3e2e8188ad8afbde38f7da158349679060`

LF normalization does not remove the difference. `MANIFEST_SHA256.txt` contains a
single digest rather than a file ledger; file verification therefore uses
PACKAGE_MANIFEST. Duplicate `(1)` release files also exist. Preserve them pending
review; they are not authoritative replacements. Compare the changed document with
the sealed RC2 artifact (recorded ZIP digest
`b19e2d71c94aa3ad4c28e52b2c7276a69ee42c965493bd1ec5c04378029b91d1`). The source ZIP
was not located or verified in this tranche. Restore or qualify a separately versioned
canonical source through an explicit review; never edit a manifest just to pass.

v1.0.10 requires per-family porting to `run_evaluators` / `should_execute`. Preserve
raw outcome, execution_status, recursive qualification, blocked_by and
allows_dependent_claim. A diagnostic PASS cannot authorize downstream claims or reveal.
Independent available evaluators should still run after a scientific FAIL. Integrity,
commitment and genuinely unavailable-data failures remain fail-closed.

## PKLSA qualification and selection

The inspected active view is under E010-v0.3.1:
`E010_PKLSA_Multiseed_View_v0.3.4-outputs/ACTIVE_ATLAS_INDEX.json`.
SELECTION_RELEASE names a v0.3.4-hotfix1 logical view, not new science qualification.
All five referenced source index hashes match current production files. All 42 active
topology directories exist: 6 historical PASS, 36 historical FAIL. Historical FAILs
must remain visible and can support negative/diagnostic studies; selection alone does
not make all 42 qualified for every hypothesis.

The inventory does not verify individual carrier payload hashes, convergence,
topology identity evidence, provider independence or physical source admissibility.
Those are mandatory per-input checks before a science run. Follow ACTIVE_ATLAS_INDEX
and enforce admitted carrier identifiers; do not recursively scan all atlas sources.
Pin the index, source release, carrier payloads, admission decisions and required
provider manifests in each new preregistration. Keep rejected carriers and reasons.

E010-v0.3.5 is a development Ruban-family subtrack. Its validation explicitly says
physical_dynamics=NOT_RUN and source_independent_provider_groups=1. It is not an
automatic replacement for the active view. E010/FAMILY.yaml still declares v0.3.0;
directory numeric ordering cannot resolve this discrepancy. A dataset resolver must
choose the newest release qualified for the specific observable, units, topology,
resolution, dynamics and provenance, then pin it. No qualifying source means
NOT_RUN_PREREQUISITE or UNRESOLVED, never synthetic substitution.

## Three pilot adapters

1. A011-v0.3.1 -> proposed A011-v0.4.0. Standalone geometry, Python/C++ parity and
   physical/thermodynamic input separation. Port the existing metric definitions;
   use a tiny documented geometry smoke and independent physical inputs only where
   admitted. Geometry proxy success cannot qualify energy or gravity claims.
2. A054-v0.5.1 -> proposed A054-v0.6.0. E013 stage 30 and E011 provider anchors.
   Its README requires E013-COMMON-CARRIER-MANIFEST-1; E010 is a source-native parser.
   Do not bypass E013 with an atlas directory. Audit enabled-version deduplication,
   constrained objective, stationarity, Hessian convergence and handoff requirements.
3. A065-v0.4.3 -> proposed A065-v0.5.0. Blind/seal and historical/synthetic lanes.
   Its main README retains older release headings; inspect lane-specific contracts
   and source seals before porting. Preserve D01/D02/D03 and every negative result.
   Historical analytic or synthetic 3D controls cannot become physical PKLSA evidence.

These are representative architectural candidates, not a completed dependency audit
or an assurance that the proposed source is the canonical latest. The source versions
exist on disk. Resolve registry conflicts and check destination nonexistence again
when cloning. Use new sibling directories, exclude venv/build/cache/run copies,
retain provenance links to original outputs, and hash source code/configs without
exporting private keys. Update FAMILY, hierarchy and catalog together at release.

## Planned production worker and persistence

The delivered queue stores all 75 families; only the three pilot jobs are eligible
for preflight. Other jobs are WAITING_PILOT. `preflight-next` cannot migrate, freeze,
reveal or launch calculations. BLOCKED jobs are not automatically retried. Reinspect
in a new state directory after corrections, preserving this evidence snapshot.

The next implementation tranche must add reviewed family adapters and a production
transactional store (SQLite on a local non-synchronized disk is recommended). Keep
the queue DB outside per-run worktrees, with a unique family/source/target/dataset/
adapter key, transactionally claimed job, owner token, lease, heartbeat, bounded
retry count and append-only event records. Never hold a DB transaction across a
calculation. On stale lease, inspect child PID and committed artifacts before retry;
use unique run IDs and create-only destinations. No automatic retry of scientific FAIL.

The current preflight uses exclusive `queue.lock`, atomic JSON replacement and unique
run result directories. A hard crash leaves the lock for manual PID inspection; do
not delete an active lock. Result publication precedes queue update; a crash between
them can repeat a read-only preflight. This mechanism is not a production lease or
distributed exactly-once implementation. Its scope is one local preflight worker.

Planned stages: QUEUED -> CLAIMED -> SOURCE_AUDITED -> CLONED_NEW_VERSION ->
MIGRATION_CHECKED -> SMOKE_EXECUTED -> SCIENCE_EVALUATED -> REPORTED. Blockers and
errors retain stage evidence and never imply a missing stage passed.

## Separate gates and completion criteria

Migration gate: source/framework/dataset hash admission; fresh sibling; correct
version metadata; explicit framework locator; unchanged observable definitions and
preregistered thresholds; blind-leak audit; contract/API validation; registry checks.

Execution gate: documented minimal environment; captured command, cwd, process exit,
stdout/stderr, timestamps, seed/backend/compiler/config hashes; narrow regressions,
representative smoke, relevant Python/native parity. NaN/Inf and missing outputs are
explicit failures. Exit zero alone does not certify a scientific gate. An exception
is an invalid run, not a negative scientific finding. Full campaigns remain excluded.

Scientific gate: per-falsifier observable, prior acceptance criterion and uncertainty
handling; input physical authority; topology/source identity; required spatial/time/
solver/core convergence and independent evidence. Preserve observed PASS/FAIL and
recursive qualification separately. A qualified negative result is valid evidence;
it is not a failed software migration. Unavailable prerequisites are NOT_RUN or
UNRESOLVED as defined by framework, never PASS. Reveal is explicit and separate,
reading fixed blind outputs and commitments, never recomputing selection.

Pilot acceptance requires all three migration gates and smoke execution gates to
pass, complete source hashes, tested retention/lock/recovery/reporting, and a reviewed
scientific ledger for each. Scientific FAIL or UNRESOLVED can be a correctly handled
outcome but cannot authorize positive downstream claims. Approve scheduling only
after reviewing these actual artifacts. The existing pilot does not meet acceptance.

## PDF and central progress

Use framework report-only generation from immutable summaries for migrated science
runs; never rerun physics to produce a report. Each PDF must show source/new version,
run ID, pinned framework and dataset hashes, assumptions/units, gate definition,
observed outcome/execution/qualification, exclusions, convergence, numerical limits
and claim boundaries. Publish create-only PDF and output ZIP with SHA-256. Separate
BLIND and REVEALED artifacts and exclude private material.

The delivered `render_reports.py` generates three preflight-only PDFs from the fixed
JSON results using reportlab. It is separate from the scientific framework renderer
and cannot certify a run. Source-index evidence is embedded in result.json. Central
progress is `queue.json`; results are under unique `runs/<id>/` directories. Future
production must add artifact/PDF hashes and validation evidence to its event ledger.

## Local environment and Scheduled design (inactive)

Required host: native Windows with the full local project and dataset paths,
readable sealed inputs, writable new-version/output/state locations and sufficient
disk space for sibling code and fresh results. Use a dedicated local worker checkout
plus central state outside disposable worktrees; explicitly provision untracked atlas
data rather than assuming a new Git worktree contains them. Do not launch a science
job in a cloud container missing local paths.

Observed here: Python 3.13.9; framework .venv exists; MiKTeX pdflatex, g++ and Poppler
are on PATH. `cl` and `icx` are not on this shell PATH; this does not prove MSVC/oneAPI
are uninstalled. Capture their documented development environments when an adapter
needs them, then test actual link and worker runtime. Native checks were not rerun.
Framework requires numpy, pytest, pybind11, setuptools and wheel; honor per-package
pins in isolated environments. The bundled PDF runtime provides reportlab. No API
key or paid API dependency is required by this preflight.

Official documentation checked 2026-10-26:
https://learn.chatgpt.com/docs/automations
https://learn.chatgpt.com/docs/get-started-with-work

Project-scoped Scheduled runs require the computer powered on, desktop app running
and project present. A web/cloud schedule alone does not retain this local folder.
Local computer access with Work Cloud additionally depends on workspace rollout and
an online connected computer; its availability was not verified for this account.
Use a project-scoped local schedule only after validating the worker end to end.

Recommended initial cadence after pilot approval: once daily, 09:00 Europe/Amsterdam,
max one claimed falsifier per invocation, no overlap, bounded adapter-specific time/
memory/thread limits, and no full campaigns. Cadence is a proposal, not configured.
Record default model/effort rather than assuming an account entitlement. If a worker
is active, skip that tick. On missing local resources, stop with a recorded blocker;
do not fall back to cloud science. Notify on completion, failure, changed blockers
or required user action; stay quiet on unchanged/non-actionable state.

Saved prompt design for the future schedule: verify pinned repo/state and source
integrity; claim at most one pilot-approved job; create a new sibling version with
its reviewed adapter; run only its admitted smoke budget; record the three distinct
gate axes; render from fixed outputs; preserve all predecessors; never commit/push,
reveal, expand to full campaigns, or alter thresholds automatically. Fail closed if
the adapter, dataset admission or pilot acceptance is absent.

No schedule was created or activated, and no account scheduling access was tested.

## Reproduce this tranche

From repository root, using Python 3:

```powershell
python -m unittest discover -s 07_scripts/sst_migration -p test_preflight.py -v
python 07_scripts/sst_migration/preflight.py init --state <new-evidence-directory>
python 07_scripts/sst_migration/preflight.py preflight-next --state <new-evidence-directory>
python 07_scripts/sst_migration/preflight.py status --state <new-evidence-directory>
```

Call preflight-next three times to inspect the three candidates, one per call. Run
`render_reports.py --state <directory>` in an environment with reportlab. It refuses
to overwrite an existing PDF. Initialization refuses to replace an existing queue.
Tests cover overlap rejection, manifest traversal and single-job fail-closed behavior.
These tests qualify preflight safety only, not the scientific pipeline.
