# A065 v0.3.2 — numerical resolution and authentic Fremlin propagation

## Provenance and preserved evidence

The v0.3.1-r1 D01/D02/D03 input files and all four SHA-256 seal/commitment documents are **byte-identical**. This version introduces a new versioned preregistration `preregistration/QUALIFICATION_V032.json`; it is NOT part of the old three source seals. Its SHA-256 is recorded in the newly frozen official v1.0.7 science contract, and in `QUALIFICATION_V032.json` results.

## Numerical experiment

Input: authenticated KnotPlot `3_1` N300; no new geometry provider. N75 and N150 remain original subsamples. N600 interpolates one midpoint between each original N300 pair using periodic cubic Catmull–Rom (-1,9,9,-1)/16; all original N300 positions are exact anchors. The **same** regularized midpoint-segment Biot–Savart kernel is used with Γ=1, ε=.12, T=.04. RK4 step-count ladder 4, 8, 16. Errors are RMS coarse-vs-fine final point mismatch / RMS coarse-grid displacement. All alignment uses inherited coordinate order; do not minimize by rotations or translations.

The historical 75–150 FAIL survives in original G2. Newly added independent scientific gates G10 (refined numerical spatial) and G11 (Fremlin numerical provider readiness) depend only on G1, not G2, so a failed coarse gate doesn't suppress diagnostic work. A G10 PASS is only discretization evidence, NOT a claim of physical convergence or Euler dynamics.

## Independent Fremlin dynamic lane

Fremlin upstream E010 record A006 CAR_d8a316361e0941af; raw source expected at `03_data/A_knots/02_fourier/resources_swirl/3_1/knot.3_1u.short` (or override `SST_A065_FREMLIN_PATH`); source SHA-256 must be `73cd5304e79a9cf52b71c88d1d7ebc21948a6d87526b0e95ba5aa6f257150e80`. The source is **not** embedded in public ZIP. The per-run `PROVIDER_MANIFEST.json` is written once, and raw bytes are re-verified on every interpretation. The separately authored C++17 solver reads the N118 Fremlin coordinates and produces actual t=T trajectories at time step counts 4/8/16; also evaluates N59 vs N118. Its outputs are tracked by hash with example coordinate triples. A source mismatch is never replaced by a generated Fourier proxy. Every provider outcome stays simulation-class and **does not imply a second independent physical Euler provider**, Maxwell/material closure, or Casimir predictions.

`SIMULATION_QUALIFIED` means only correct byte-source identification + executed independent C++ code + spatial/time numerical qualification of the **same reduced ODE**. It is not full Euler or a model-independent physics replication. C++ compiled binary is not silently replaced by Python when unavailable.

## Running

`run_all.cmd QUALIFY` performs sealed analytic pilot, fixed-core spatial qualification, and Fremlin C++ lane when its real source and C++ compiler exist, then publishes a self-contained LaTeX/PDF. `run_all.cmd FRAMEWORK` uses the installed untouched `SST_Falsifier_Framework_v1.0.7`, adds only G10/G11 in a newly generated, frozen instance, and preserves G2=FAIL. Every invocation gets unique run ID and create-only exports. `run_all.cmd ALL` runs regression tests first.

## Remaining research

Independent complete 3D Euler time stepping/pressure-Poisson, Kelvin/Floquet spectra, validated physical boundary conditions, convergence in regularization parameter, physically measured or derived material susceptibility, and held-out measurements all remain unvalidated.
