# A075 v0.1.0 — Hydrodynamische resonante invanging

## Status
`DEVELOPMENT_ONLY` — genuine SST Falsifier Framework v1.0.10 protocol and run infrastructure, but **no full Euler physical certification**. This package does not vendor or modify the canonical framework. The frozen shared framework must be available locally.

## One command on Windows
From this version directory: `run_all.cmd FREEZE`, then `run_all.cmd BASIC` and/or `run_all.cmd FULL`.
Do not run `REVEAL`: G8 (physical Euler provider) is unresolved. `run_all.cmd` sets the shared framework location under `C:\workspace\projects\SST-Workbench\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.10`. The `SST_FALSIFIER_FRAMEWORK_ROOT` env variable overrides this.

## Scope and source discipline
- A021-v0.4.0: borrow method of mode decomposition and separation of numeric versus physical recurrences; no trefoil conclusions or presumed restoring force carried over.
- A032-v0.1.0: borrow regularized midpoint kernel, pairwise Hamiltonian proxy, no-loss and observation-window controls; neither Euler pressure-Poisson closure nor full fluid energy flux borrowed.
- New numerical model: two **fully coupled** regularized closed vortex centerlines with circular control geometry and **no imposed symmetry filter** on perturbations. This is a non-dissipative filament screening, not full incompressible Euler proof.
- Tests do not assume an absorbed photon or quantum correspondence; no pentagonal selection.

## Output
Framework creates unique BLIND run ID, writes gate ledger and PDF when latexmk is installed, creates source and output manifests, and preserves old output roots.
The scientific source and input checksums are stored in `SOURCE_PROVENANCE.json` and `source_evidence`.

## Advancement rule
If and only if G0-G5 are qualified under fixed physical time and a genuine physical field provider measures local energy and flux on a material control volume can G3/G8 be considered for positive physical qualification. Native C++ or GPU parity is not claimed by this Python-only v0.1.0.
