# A060 — Dynamical Topology & Coherence Blind Falsifier v0.1.0

Framework target: **SST Falsifier Framework v1.0.6 CANONICAL_FROZEN**

## Why A060
Drive audit (2026-10-08) shows A001–A058 families physically present in `01_research/A_falsifiers`; the user reports A059 is already allocated. A060 is therefore used rather than colliding with A056/A057/A058.

## Scientific fusion
A060 deliberately does not replace its upstream falsifiers. It fuses their *orthogonal observables*:
- A023/A031: RPO + true Floquet/monodromy discipline.
- A033: measured return-phase / causality and fixed-core null logic.
- A051: spontaneous time-reversal phase locking and gauge-invariant two-mode order parameter.
- A053: topology-transition tournament discipline and no target-aware topology surgery.
- A055: blind topological spectrum, framework v1.0.6 integrity/provenance discipline.
- A056: phase-topology-aware circular/Fourier spectral representation and fresh confirmatory inputs.

External methodological controls:
- Tian et al. (2019): Loschmidt/return amplitude, rate function, phase jump, accidental-vs-protected DPT caution.
- Barkhofen et al. (2023), arXiv:2301.05428: Floquet/chiral spectral pairing, time-staggered response, static disorder vs dephasing.

## Primary question
Does a PKLSA-derived knot/link dynamical system exhibit a **resolution-converged, perturbation-robust, coherence-dependent dynamical-topology signature** that cannot be explained by finite-size zeros, generic spectral interference, static localization, target-aware construction, or an imposed symmetry?

No SST constants, particle labels, expected phase, expected frequency, or preferred topology may enter blind scoring.

## Input contract
A `.npz` case may contain:
- `t`: shape (T,)
- `psi`: complex shape (T,D), preferred; or `modes`: complex shape (T,M)
- optional `monodromy`: complex shape (D,D)
- optional `topology_code`: anonymous integer/string only
- optional `resolution`: integer
- optional `condition`: one of `baseline`, `static_disorder`, `dephasing`, `topology_preserving`, `topology_changing`, `null`

If only `modes` is supplied, it is used as the state vector.

## Gates
G0 provenance/input integrity.
G1 norm/finite-data/numerical sanity.
G2 return-amplitude DPT candidate: minima of |G(t)| plus rate-function peaks; candidate only, never sufficient.
G3 finite-size/resolution convergence: candidate critical times must converge and minima deepen/non-disappear.
G4 Floquet spectral-pairing test: tests conjugate/inverse and pi-shift pairing *without assuming chiral symmetry*.
G5 time-odd two-mode phase-locking observable (when >=2 modes are supplied), including time-reversal antisymmetry diagnostic.
G6 static-disorder robustness: signature survives quenched/static perturbation.
G7 dephasing challenge: coherent signature is selectively suppressed by time-dependent phase randomization.
G8 accidental-structure rejection: null/topology-preserving controls must not reproduce the full signature at comparable strength.
G9 cross-geometry/topology robustness/class separation.
G10 composite verdict.

**Continue-on-fail:** every computable gate runs even if an earlier gate fails. A failure cannot be silently converted to SKIP. Missing prerequisites become INDETERMINATE.

## Commands
```
run_all.cmd SELFTEST
run_all.cmd BASIC path\to\case_or_directory
run_all.cmd FULL  path\to\case_or_directory
```

Outputs are written under `outputs/<timestamp>_<mode>/` and include per-case JSON/CSV plus `blind_summary.json`.

## Interpretation
A060 does not claim that a DPT, pi phase jump, Floquet pair, or Fourier peak proves an SST particle. The strongest positive label is `SUPPORTED_TESTED_DOMAIN`; otherwise results are `FAIL_TESTED_DOMAIN` or `INDETERMINATE_*`.
