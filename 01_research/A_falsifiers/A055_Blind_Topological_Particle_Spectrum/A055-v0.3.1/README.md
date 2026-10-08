# A055 — Blind Topological Particle Spectrum Falsifier v0.3.1

A055 v0.3.1 is the method-corrected follow-up to v0.3.0 and is implemented as a thin scientific instance of **SST Falsifier Framework v1.0.4 CANONICAL_FROZEN**.

## Purpose

v0.3.0 showed that using the signs of the imaginary parts of eigenvalues as a counterpropagation test is non-discriminating for a real projected Jacobian: complex eigenvalues occur automatically as conjugate pairs. v0.3.1 therefore measures propagation direction from the **signed spatial arclength-Fourier content of reconstructed complex eigenfields**, while using only positive temporal frequency representatives.

The primary blind question is whether any anonymous three-component compound contains two distinct positive-frequency, Kelvin-dominated traveling modes at the same registered harmonic, with opposite spatial propagation and preregistered frequency matching, reproducibly in at least two circulation sectors.

## Upstream evidence

Production FULL/CERTIFY requires two already completed sealed sources:

1. A054 v0.2.0-r2 full three-component compound certification;
2. A055 v0.3.0 full output as an isolated-centerline control baseline.

v0.3.1 **never launches A054 automatically**. Missing or ambiguous upstream evidence is `UNRESOLVED` and stops the scientific chain fail-closed.

## Main corrections relative to v0.3.0

- physical direction is inferred from signed spatial harmonics, not the sign of `Im(lambda)`;
- conjugate eigenmodes cannot manufacture a bidirectional pair;
- the fine-resolution upstream Jacobian is recomputed and its eigenvalue multiset must match the sealed stored spectrum;
- historical control cells are deduplicated by `(case, provider, mode, N)`;
- reveal-only architecture/component comparisons are paired within frozen assignment/provider strata;
- no pooled unpaired median is used as the primary component-identity statistic;
- nonlinear promotion still requires the same pair-bearing sector to have sealed upstream spatial convergence and an accepted RPO; Floquet remains conditional on that RPO.

## Frozen thresholds

- relative temporal-frequency floor: `1e-7`;
- Kelvin-basis fraction: `zeta >= 0.50`;
- harmonic participation: `eta >= 0.50`;
- directional purity: `|chi| >= 0.60`;
- oscillatory quality: `|Re(lambda)| / |Im(lambda)| <= 1.0`;
- opposite-direction frequency asymmetry: `A_omega <= 0.25`;
- anonymous recurrence: qualified pair in at least 2 circulation sectors;
- sealed-spectrum recomputation error: `<= 1e-8`;
- Python/C++ signed-power parity: relative L2 `<= 1e-10`.

The machine-authoritative protocol is the framework-frozen bundle in `preregistration/FROZEN_PROTOCOL.json`.

## Canonical locations

Instance:

```text
01_research\A_falsifiers\A055_Blind_Topological_Particle_Spectrum\A055-v0.3.1
```

Framework:

```text
06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.4
```

## Run

Recommended production command:

```bat
run_all.cmd full C:\workspace\projects\SST-Workbench
```

Blind-only production run:

```bat
run_blind_only.cmd FULL C:\workspace\projects\SST-Workbench
```

`run_install.cmd` creates/updates the local virtual environment; `run_10_selftest.cmd` runs the instance tests and framework selftests before science.

### Local Windows execution adjustments (2026-10-07)

The runtime is stored in the sibling `.a055-v0.3.1-runtime` directory so installed
third-party packages are outside the public instance blind scan. The selftest
runner locates the canonical framework relative to this instance. Windows native
loading uses an extended path for deeply nested isolated upstream runners.

REVEAL follows the supplied framework policy. Frozen scientific inputs and gate
thresholds are unchanged. A blocked reveal leaves the BLIND package available.
Execution logs and local source-change hashes are stored in the sibling
`A055-v0.3.1-execution` directory. The supplied release manifest is retained as
the original package reference.

## Interpretation boundary

A signed bidirectional traveling pair is evidence only for a linear projected traveling-wave sector of the registered finite-core filament model. It is not a particle identification. A mechanism is promoted only if the same sector also passes the frozen upstream spatial-convergence and nonlinear RPO gates. Reused simulation sources are not independent physical replication.
