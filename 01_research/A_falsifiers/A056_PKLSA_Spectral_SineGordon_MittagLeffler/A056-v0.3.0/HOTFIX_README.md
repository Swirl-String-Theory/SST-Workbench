# A056-v0.3.0 hotfix 1 — Windows provider entry point

## Symptom

The first Workbench run of `run_e010_filament.cmd` stopped before reading E010 data with:

```text
ModuleNotFoundError: No module named 'a056_provider'
```

## Root cause

`python tools\build_e010_provider.py ...` makes Python use the `tools` directory as `sys.path[0]`. The sibling package `a056_provider/` is one directory above it, so it is not importable unless the instance root was already on `PYTHONPATH`.

## Fix

1. The three `run_e010_*.cmd` launchers now call the package-safe module entry point:

```text
python -m a056_provider.campaign ...
```

2. `tools/build_e010_provider.py` now explicitly bootstraps `Path(__file__).resolve().parents[1]` before importing `a056_provider`, so direct use remains supported.
3. A subprocess regression test verifies the direct-script entry point.

## Scientific status

This hotfix changes launcher/import mechanics only. It does **not** change the frozen science contract, provider configuration, equations, thresholds, blindness rules, evidence classes, gate plan, or SST Falsifier Framework v1.0.4. The frozen protocol bundle remains:

```text
cc53314d255085ca2b23efa045b1d99d3e0c048b1af7687cc22840cd626467ae
```

## hotfix 2 — fail-closed reveal orchestration

Real E010 provider campaigns can legitimately stop before discovery (for example when G1/G2 does not PASS). Framework v1.0.4 correctly refuses REVEAL unless the frozen `blind_policy.json` prerequisite gate has a terminal PASS/FAIL state. The previous A056 launcher called REVEAL unconditionally and therefore converted this scientific fail-closed state into a traceback.

Hotfix 2 adds an instance-local `REVEAL_IF_ALLOWED` preflight. If reveal is not eligible, the launcher exits cleanly, records `REVEAL_DECISION.json`, preserves the BLIND package and does **not** expose the private E010 provider mapping. Stale reveal artifacts from an older run of the same version are purged before a new blind campaign. The provider reveal helper now requires verified framework reveal state when launched automatically.

No frozen scientific contract, threshold, gate definition, provider configuration, equation, or commitment changed; the frozen protocol hash remains unchanged.

## hotfix 3 — Windows runtime-directory reset

A repeated real-provider run can encounter `PermissionError: [WinError 5] Access is denied` while `shutil.rmtree()` removes `data\\runtime_e010_*`. On Windows a transient antivirus/indexer/Explorer handle may permit deletion of the directory contents while preventing the final `os.rmdir()` of the directory root. The provider does not need to delete that root.

Hotfix 3 replaces root-level `shutil.rmtree(runtime_dir)` with a fail-closed `reset_runtime_directory()` operation that:

1. keeps the runtime directory root in place;
2. removes every stale child before a new provider campaign;
3. clears read-only attributes before deletion;
4. retries transient sharing/permission failures with bounded backoff;
5. applies the same policy to the private provider-reveal directory.

If a child remains genuinely locked after the retry budget, the run still fails before scoring with the exact locked path. No partially stale provider directory is accepted.

This is an execution/workspace hotfix only. The frozen science contract, provider configuration hashes, equations, thresholds, evidence classes, blindness policy, gate plan, and framework v1.0.4 remain unchanged.

## Hotfix 4 - G2 diagnostic retention

A real E010 filament run can legitimately terminate at G2 before the normal case-results table is written. Hotfix 4 does **not** alter G2, its POD definition, thresholds, model competition, or reveal policy. It only persists opaque per-case POD metrics as `A056_G2_DIAGNOSTICS.json` and `A056_CASE_RESULTS_PARTIAL.csv` before the fail-closed return. `run_diagnose_g2.cmd` provides a read-only diagnostic over an already generated provider directory, so the expensive provider evolution need not be rerun just to inspect the split-window POD overlap.
