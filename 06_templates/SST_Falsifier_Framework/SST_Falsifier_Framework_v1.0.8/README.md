# SST Falsifier Framework v1.0.8

**Maintenance release candidate (local tests PASS).** v1.0.7 remains the historical `CANONICAL_FROZEN` parent and was not modified. Deploy v1.0.8 alongside it; only retarget future falsifiers after local verification. Existing falsifiers should retain their pinned framework.

## Non-overwriting run exports

Each new `BASIC` / `FULL` / `CERTIFY` blind run receives a persistent `RUN_ID.json` value: `YYYYMMDDTHHMMSSffffffZ-rrrrrrrr` (UTC, random hexadecimal suffix). The pipeline continues to write to its familiar `Instance/<project>_<version>-outputs/` path. **Before** a new blind run begins, any old working output directory is **renamed**, not deleted, to `Instance/<project>_<version>-outputs__<previous-run-id>/`. A pre-v1.0.8 directory is archived with a `LEGACY-...` name.

Publication names alongside the instance folder:

- `<project>_<version>-outputs__<run-id>_BLIND.zip`
- `<project>_<version>-outputs__<run-id>_REVEALED.zip`
- `<instance-folder>__<run-id>_BLIND_FALSIFIER_REPORT.pdf`
- `<instance-folder>__<run-id>_REVEALED_FALSIFIER_REPORT.pdf`

BLIND and REVEALED use the **same** run ID. `REVEAL` and `REVEAL_IF_ALLOWED` do not start a new run, and require the current `RUN_ID.json`. Each PDF and ZIP is created exclusively and fails rather than replacing an existing file. Existing legacy PDF/ZIP files are never removed. In-tree `REPORT_RENDER_BLIND.json` and `REPORT_RENDER_REVEALED.json` are separate; on reveal `AUTO_RESULTS_BLIND.tex` is retained before producing the revealed auto-results text.

### Concurrency and interrupted runs

A lock file named `.<instance-folder>.sst-run.lock` is created exclusively in the parent folder. If a run crashes and leaves a lock, inspect the running process and the output files before manually removing it. Never remove a lock while a process is still running. A failed/partial run remains on disk and is archived on the next blind execution. Running `FREEZE` and `SELFTEST` does not rotate output directories.

**Scope:** The framework guarantees run-level preservation and non-overwriting publication artifacts; it does not intercept arbitrary scratch file replacements made inside a scientific pipeline *during a single run*. Pipelines requiring multiple revisions within one run must use their own unique checkpoint names.

### Verification on Windows

Install in `SST-Workbench\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.8` and run:

```cmd
run_all.cmd SELFTEST
run_all.cmd BACKENDS
```

For a generated falsifier, `run_all.cmd BASIC` or `FULL` follows the instance's own script contract. Retain the `.sst_framework_root` relative pin to v1.0.8. `REVEAL` is available only after the registered reveal-eligibility checks. For a local end-to-end two-run exercise with LaTeX installed, execute `python tools/smoke_run_identity.py` from the framework folder.

See `docs/EXPORT_RETENTION_POLICY.md`, `VALIDATION.md` and the immutable `PARENT_CANONICAL_FREEZE.json` for details.
