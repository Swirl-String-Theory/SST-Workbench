# Independent Finite-Core Spectral Selector v0.1.0

A blind, dimensionless C++/pybind11 experiment for finite-core incompressible vortex dynamics.

This package is intentionally **independent of any model-specific physical constant or external target**. The numerical kernel knows only:

- core radius unit `a = 1`;
- circulation/time unit `Gamma = 1`;
- dimensionless ring radius `R/a`;
- dimensionless periodic spacing `L/a = exp(q)`;
- discretization, regularization and finite-difference controls.

No SI constants are accepted by the CLI. No external target scale is built into candidate detection.

## Physics implemented

The native kernel discretizes a closed vortex ring into straight segments and evaluates a regularized Biot-Savart law. Default regularization is Rosenhead-Moore,

`dv = (1/4pi) dl x r / (|r|^2 + a^2)^(3/2)`, with `a=1` and `Gamma=1`.

Periodic image cells are included up to `image_shell`. At every evaluation the best-fit rigid translation and rigid rotation are removed. The Jacobian is formed only in ring-normal and binormal perturbation directions, eliminating tangential reparameterization modes. NumPy computes its eigenvalues; the expensive finite-difference columns are evaluated in parallel inside C++.

This is an **exploratory scale-selector falsifier**, not a proof that a detected spectral feature sets a physical macroscopic scale.

## Quick start (Windows)

```bat
run_native_preflight.cmd
run_all_checks.cmd --threads 16
run_quick.cmd
run_full.cmd
```

The default blind campaign scans `q=2.5..40` in steps of `0.5`. For a denser campaign:

```bat
run_blind_campaign.cmd --threads 16 --n-nodes 32 --q-min 2.5 --q-max 40 --q-step 0.25 --fd-eps-over-core 1e-4 --out-dir audit_full
```

Then run the robustness ladder:

```bat
run_refinement.cmd --threads 16 --q-min 2.5 --q-max 16 --q-step 0.5 --out-dir audit_refinement
```

## Outputs

`run_blind_campaign.py` writes:

- `independence_manifest.json`
- `scan.csv`
- `scan.json`
- `candidate_scales.json`
- `audit_summary.json`

Do **not** compare candidate locations to an external target until these files are frozen/hashed. See `INDEPENDENCE_PROTOCOL.md`.

## Candidate interpretation

A reported candidate is only an internally defined event in `L/a`. It is promoted only if it survives:

1. node refinement;
2. finite-difference refinement;
3. image-shell refinement;
4. core regularization change;
5. equilibrium-residual gate;
6. later geometry/topology out-of-sample tests.

No candidate is forced to exist. A null result is a valid result.

## Dependencies

- Python 3.10+
- NumPy
- pybind11
- C++17 compiler

The template's hash-based native rebuild and pure-Python fallback are retained.

## Wide-range numerical safeguard

The periodic-image Jacobian is evaluated separately from the isolated-ring Jacobian and only added afterwards. This avoids subtracting tiny image effects from O(1) self-dynamics at large `L/a`. The image interaction is also projected onto the six-dimensional isolated-ring near-null subspace, so its normalized structure can still be inspected when its absolute amplitude is extremely small.

## Fast Windows runners

- `run_quick.cmd` — coarse blind scan.
- `run_full.cmd` — dense blind scan through the full preregistered dimensionless hierarchy window.
- Both accept extra CLI flags after the defaults; `run_blind_campaign.cmd` remains the fully explicit runner.

## References

Copy-ready LaTeX `\bibitem` entries are in `REFERENCES.tex`.
