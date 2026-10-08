# A054-v0.4.0 — Mechanism Injection Falsifier

**Framework:** SST Falsifier Framework **v1.0.4 CANONICAL_FROZEN** (thin instance; framework is not vendored or patched).

## Question
A054-v0.2 found strong geometric coherence but no restoring/ringdown-certified branch. v0.4.0 asks whether a preregistered reduced closure can supply the missing dynamical confinement without changing geometry-specific parameters or weakening any v0.2 hard gate.

## Arms
`BASE`, `CORE`, `ELASTIC`, `CORE_ELASTIC` form a 2×2 mechanism factorial. `CORE` is a finite-core repulsive-core/attractive-shoulder stress surrogate. `ELASTIC` is a curvature/bending surrogate. Both are mapped through a tangent cross-product and RMS-normalized to the initial Biot–Savart velocity scale. They are effective reduced closures, not first-principles derivations.

## Sources
- Discovery: exact 72 anonymous geometries from the frozen A054-v0.2 FULL campaign.
- Held-out confirmation: 7 source-native three-component KnotPlot link geometries from A054-v0.3, re-encoded under opaque IDs. Semantic identities exist only under `PRIVATE/` and are commitment-bound.

## No per-candidate fitting
Each active mechanism uses the same global gain grid. One gain per arm is selected using discovery only and transferred unchanged to confirmation. Candidate-specific or topology-specific gains are forbidden.

## Run
```cmd
run_all.cmd
run_all.cmd FULL
```
The Workbench root defaults to `C:\workspace\projects\SST-Workbench`; an explicit second argument or `SST_WORKBENCH_ROOT` overrides it.

If held-out recovery is found, run the full frozen-v0.2 resolution/native certification:
```cmd
run_certify_selected.cmd
```
Reveal remains separate:
```cmd
run_reveal.cmd
```

## Interpretation boundary
A simulation-level recovery identifies a candidate reduced mechanism worth deriving/test-driving. It does **not** establish a particle identity, a physical shear modulus, a first-principles Euler pressure closure, or SST particle physics. Framework G7 physical replication remains closed until eligible independent physical evidence exists.
