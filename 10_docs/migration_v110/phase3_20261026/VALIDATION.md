# Phase 3 - Framework source qualification and A011 controlled migration

Date: 2026-10-26. Scope: P01 and the A011 P05 geometry adapter only.

## Result

* 3A PASS: separately admitted clean Framework v1.0.10 CANONICAL_FROZEN source,
  112/112 canonical manifest entries verified. Complete extraction inventory is
  byte-pinned; content-addressed source/distribution files are read-only and checked
  on adapter use. The original installed framework and its local Markdown variant
  remain untouched. No historical manifest was regenerated.
* 3B PASS_GEOMETRY_ADAPTER: A011-v0.4.0 created beside v0.3.1; exact admission,
  framework ledger, source pins, immutable adapter geometry protocol and bounded
  geometry/native diagnostic runner added. Inherited geometry/native definitions
  and parity tolerances are unchanged. Parent manifest/build info are retained as
  provenance, not presented as a new release's source manifest.
* Execution PASS_BOUNDED_GEOMETRY_SMOKE: three admitted single-component VECT seeds,
  each 300 source points, N=64 and N=128, one CPU thread, no GPU, no RNG, no reveal.
  Process exit 0, measurement duration about 1.79 seconds within 120-second budget.
* Science UNRESOLVED_MISSING_PHYSICAL_INPUTS. G5 raw PASS remains DIAGNOSTIC_ONLY,
  `allows_dependent_claim=false`; physical G3/G4/G7/G8 were not run. Two geometry
  resolutions are sensitivity diagnostics, not convergence or physical certification.

The adapter uses the actual v1.0.10 `GateLedger.run_evaluators` and protocol hashing
APIs. Its runner is an explicitly scoped geometry adapter. The full framework
`run_mode` BLIND/REVEAL workflow and private-target FREEZE were not executed.

## Commands and observed validation

All commands ran from `C:\workspace\projects\SST-Workbench`.

1. `python -B 07_scripts/sst_migration/phase3_prepare.py qualify`
   - Exit 0; canonical archive matches Phase 2 digest; every one of 112 entries
     verified before extraction and again afterward. The full extracted inventory
     is bound by `framework_source_qualification.json`, written create-once.
2. `python -B 07_scripts/sst_migration/phase3_prepare.py clone`
   - Exit 0; required 3A PASS and reverified its bytes before creating v0.4.0.
     Captured all 406 predecessor files and excluded-pilot source/metadata pins.
     Copy excludes prior outputs, ZIPs, build caches and environments.
3. `python -B 07_scripts/sst_migration/phase3_configure_a011.py`
   - Exit 0; deterministic seed plan and unchanged tolerances registered before tests
     or measurements. Native source stamp verified using the original Windows path
     encoding. Exact existing cp314 binary retained; no rebuild or silent fallback.
   - Dedicated 98-file geometry protocol created with the qualified framework's
     `build_protocol_bundle`; science contract and gate-plan validators pass.
4. `python -B 07_scripts/sst_migration/phase3_run_checks.py tests`
   - CPython 3.14.3 subprocesses, `-B`, cache disabled, fixed one-thread environment.
   - 14 framework gate/protocol/non-short-circuit tests passed, exit 0.
   - 35 A011 tests passed, exit 0: inherited regressions plus genuine-admission,
     modified-contract/source rejection, path containment, create-only outputs and
     physical-prerequisite non-promotion tests. No skipped native parity test.
5. `python -B 07_scripts/sst_migration/phase3_run_checks.py smoke`
   - Required both successful test records first. Exit 0 under enforced 120-second
     subprocess timeout. Exact command, cwd, timeout, duration and log captured.
   - Six seed/resolution parity comparisons pass original tolerances: velocity
     rtol=1e-11 / atol=1e-12; writhe and distance absolute differences <1e-11.
   - Maximum velocity absolute difference 2.220446049250313e-16; writhe and distance
     differences 0. No NaN/Inf or execution error. Source/admission rechecks pass.
6. `python -B 07_scripts/sst_migration/phase3_package_source.py`
   - Exit 0; source archive reopened and all 159 source-manifest entries verified.
     Test and command logs copied into results. Pre-report machine evidence sealed
     independently of PDF/archive publication to avoid circular hash dependencies.
7. `render_phase3_a011.py` using bundled Python/reportlab
   - Exit 0; four-page standalone PDF. Reopened with pypdf; all four pages rendered
     with Poppler and visually inspected. No clipping/overlap or missing glyphs.
     Local Poppler unused-font-map warnings are retained in `poppler_render.log`.
8. `python -B 07_scripts/sst_migration/phase3_publish.py`
   - Exit 0; predecessor's 406 files unchanged. A054 64 source files, A065 160 source
     files and both FAMILY metadata files unchanged; private escrow and bulky old
     run/output copies were never written. Old framework document unchanged.
   - Result archive reopened, all payload hashes and CRCs verified, SHA-256 sidecar
     created. Source and result ZIPs are create-only and no archive was overwritten.
   - Only A011 registry records and A011 FAMILY metadata changed. Other hierarchy/
     catalog nodes are structurally identical. Historical family reproducibility
     and scientific fields remain intact.
   - Existing queue updated under its exclusive lock using atomic replacement;
     exact prior queue saved. All other queue jobs are unchanged, including A054/A065.
     `scheduling_enabled=false`, `pilot_validated=false` (the three-pilot batch is
     not complete). A011's three status axes are stored separately.
9. `python -B -m unittest discover -s 07_scripts/sst_migration -p 'test_*.py' -v`
   - Exit 0; 13 migration/evidence/publication tests passed after publication.
   - The historical Phase 2 assertion now reads the exact saved pre-Phase-3 queue
     and Phase 2 decision ledger. It no longer asserts that an authorized later
     successor must never exist. Its previous test source is retained separately;
     no Phase 2 evidence manifest was rewritten.

Total: 49 implementation/framework tests before smoke, then 13 queue/publication
regressions. No full physical campaign, parameter fit, target reveal or GPU run.

## Evidence and hashes

`HASHES.json` gives the qualified framework distribution/tree, new A011 source
archive/tree/protocol and result ZIP/PDF digests. Archive sidecars are adjacent to
their ZIPs. `gate_overview.json` and `GO_NO_GO_A054.json` record the narrow migration
qualification and explicit next-tranche decision. Source and result archives have
their own complete manifests and fixed byte inventories.

All Phase 1/2 snapshots and historical manifests remain preserved. Earlier artifact
digests for live registry/queue paths describe historical states; exact pre-change
versions are retained under `before_publication/`. This phase does not rewrite those
old digests to make the current live state appear historically identical.

## A054 decision

NO_GO_IMMEDIATE_A054_MIGRATION. The shared framework source is ready. A054 still
requires explicit P02 source admission, and its successor must satisfy P04 runtime
self-hash/E011-binding/loader-pin requirements and move off its v1.0.6 locator.
L2a1's single-provider limitation remains a scientific admission boundary. No A054
or A065 work was started. Scheduled remains off.
