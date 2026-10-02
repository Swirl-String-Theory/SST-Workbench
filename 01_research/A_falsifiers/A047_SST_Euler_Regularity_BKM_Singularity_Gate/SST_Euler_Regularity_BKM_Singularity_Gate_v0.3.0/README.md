# SST Euler Regularity / BKM Singularity Gate v0.3.0 (A047)

**E010 / PKLSA v0.3.1 source-native integration release.** A047 now consumes the latest v0.3.x PKLSA release found in the SST-Workbench: `E010-v0.3.1` (2026-09-25), rather than the historical self-contained PKLSA v0.1.1 bundle.

## What changed

- Uses the E010-v0.3.1 production `3_1` carrier/evidence graph.
- Rechecks E010 source/identity/topology gates before any Euler evolution.
- Loads original Workbench source bytes through E010's own geometry loaders.
- Rechecks both raw source hashes and E010 geometry hashes.
- Enforces the E010 G1/G2/G3 literature-hard-gate failures as exclusions by default.
- Excludes byte-identical/mirror evidence and geometry/raw duplicates by default.
- Preserves E010 independence groups as anonymous BLIND strata and reveals provenance only after the run.
- Keeps BKM resolution convergence strictly within one geometry.
- Retains the v0.2.1 Windows/MSVC `py::ssize_t` portability fix.

The inspected E010-v0.3.1 trefoil POC contains 189 qualified carriers in 7 independence groups. Under A047's default literature + duplicate guards, the inspected production ledger admits 116 unique trefoil geometries. Runtime selection is computed from the local ledgers, not hard-coded.

## Run

From this A047 directory:

```cmd
run_all.cmd C:\workspace\projects\SST-Workbench
```

or set `SST_WORKBENCH_ROOT` and run `run_all.cmd`.

Optional second argument chooses a config:

```cmd
run_all.cmd C:\workspace\projects\SST-Workbench config\e010_v031_smoke.json
run_all.cmd C:\workspace\projects\SST-Workbench config\e010_v031_basic.json
run_all.cmd C:\workspace\projects\SST-Workbench config\e010_v031_certification_template.json
```

Configs:

- `e010_v031_smoke.json`: at most one carrier per E010 independence group, N=16 software/integration smoke;
- `e010_v031_basic.json`: all default-admitted source-native `3_1` carriers, N=24 population screen;
- `e010_v031_certification_template.json`: same geometry set at N=32/48/64 for per-geometry convergence certification; expensive.

## Interpretation

`NO_CONVERGED_BKM_CANDIDATE_IN_WINDOW` means only that no admitted geometry passed the preregistered finite-window numerical escalation gate. It does not establish global Euler regularity. Likewise, E010 geometry qualification does not establish Euler/Biot--Savart dynamical stability.

See `docs/PKLSA_INTEGRATION.md`, `docs/PREREGISTRATION.md`, and `VALIDATION.md`.
