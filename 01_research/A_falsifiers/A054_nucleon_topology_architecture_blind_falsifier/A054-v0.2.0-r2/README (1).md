# A054 v0.2.0-r2 — Restoring-Force × Kelvin/Floquet Nucleon Certification

Blind-first finite-core dynamical certification extending A054-v0.1.1.

The package is deliberately adversarial: the v0.1.1 Triple-Gear `6_1-opposed` tendency is *not* given a favorable threshold. Every linked composition/permutation and every circulation sector in the preregistered cohort is passed through the same restoring, Kelvin, ringdown, RPO and conditional Floquet machinery.


## r2 execution hotfix

The scientific preregistration remains v0.2.0. r2 changes execution plumbing only. EXTENDED/FULL now preflight the isolated `a054_blind._native` OpenMP extension before candidate preparation, and the actual certification process pre-imports the same native module again before loading the solver. See `HOTFIX_v0.2.0-r2.md`.

## Scientific status

This is a finite-core vortex-filament falsifier. It does **not** derive proton/neutron masses, electric charge, QCD, Pauli statistics, or a complete nucleon field theory.

The E010/PKLSA + E011 handoff supplies source geometry/provenance only. `5_2` is currently cross-provider robust; `6_1` is explicitly provider-sensitive and is therefore carried as a provider envelope rather than collapsed into one preferred seed.

## Run

From `C:\workspace\projects\SST-Workbench\...\A054-v0.2.0-r2`:

```cmd
run_all.cmd C:\workspace\projects\SST-Workbench
```

This executes install → tests → BASIC anonymous preparation (28 cases: 24 linked mixed-assignment cells + 4 unlinked controls) → isolated blind runner → dynamical certification → blind archive. It **stops before reveal**.

Higher-cost campaigns:

```cmd
run_all_extended.cmd C:\workspace\projects\SST-Workbench
run_all_full.cmd C:\workspace\projects\SST-Workbench
```

Reveal only after blind review:

```cmd
run_99_reveal_cert.cmd <campaign_dir>
```

## Branch logic

A candidate may reach:

- `INCONCLUSIVE_NUMERICAL` — convergence failure; not a physical rejection.
- `NOT_CERTIFIED_DYNAMICAL` — one or more hard dynamical gates fail.
- `CERTIFIED_RESTORING_KELVIN_RINGDOWN_BRANCH` — converged restoring/Kelvin/ringdown hard gates pass; the relative-equilibrium residual remains diagnostic only.
- `CERTIFIED_RPO_PROJECTED_FLOQUET_BRANCH` — the hard gates pass, a nontrivial RPO is found, and the nonlinear relative time-T return map is bounded in the preregistered physical subspace.

The central integrity rule is inherited from the SST Kelvin/Floquet Workbench and A021 coupled-mode line:

> **No accepted RPO → no Floquet evaluation.** The v0.2.0 Floquet layer is the derivative of the nonlinear relative time-T return map projected to a preregistered non-rigid mode subspace; it is not an infinite-dimensional Euler stability proof.

See `docs/CERTIFICATION_PROTOCOL.md` and `docs/V020_PREREGISTRATION.md`.

## Outputs

```text
PREPARE_STATUS.json
UPSTREAM_PLAN.json
BLIND_MANIFEST.json
blind_inputs/CAND_*.npz
blind_runner/
CERT_CONFIG.json
BACKEND_QUALIFICATION.json
CERT_RESULTS_BLIND.json
CERT_ANALYSIS_BLIND.json
CERT_REPORT_BLIND.md
CERT_BLIND_SEAL.json
```

Private mapping is stored only under `_private/` and is excluded from BLIND archives.

## Lineage

The old v0.1.1 entry scripts/configs are retained under `legacy_v011/` only for audit/reproduction. The v0.2.0 scientific entry points are `run_all*.cmd`, `run_02_prepare_cert.cmd`, `run_03_certify.cmd`, and `run_99_reveal_cert.cmd`.
