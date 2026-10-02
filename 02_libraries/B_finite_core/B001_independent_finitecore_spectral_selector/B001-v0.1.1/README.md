# Independent Finite-Core Spectral Selector v0.1.1

A blind, dimensionless C++/pybind11 convergence experiment for finite-core incompressible vortex dynamics.

The numerical solver accepts **no external physical constant and no external target value**. Its internal units remain exactly:

- core-radius unit `a = 1`;
- circulation/time unit `Gamma = 1`;
- dimensionless ring radius `R/a`;
- dimensionless periodic cell size `L/a = exp(q)`.

v0.1.1 is deliberately a convergence release. It does not add a new physical closure.

## Why v0.1.1 exists

The v0.1.0 wide scan showed that useful full-spectrum structure is concentrated near the small-cell regime, while the projected periodic interaction eventually becomes comparable with finite-difference roundoff and produces spurious neutral-subspace sign changes. v0.1.1 therefore:

1. narrows the preregistered numerical campaign to the non-overlapping interval `q=2.31..4.10`;
2. adds node, periodic-image-shell and finite-difference ladders;
3. automatically refines **every** detected full-spectrum gap minimum without hard-coding a candidate location;
4. tracks eigenmodes by phase-invariant eigenvector overlap;
5. suppresses neutral-subspace candidate nomination when its interaction signal is less than 100 times the computed `eps_machine / h` floor;
6. promotes a numerical candidate only if independent convergence gates are satisfied.

The lower bound is `2.31`, rather than `2.30`, because for the default `R/a=4` the non-overlap constraint is

`q > ln(2*(R/a+1)) = ln(10) = 2.302585...`.

## Full convergence campaign

Windows:

```bat
run_native_preflight.cmd
run_all_checks.cmd --threads 16
run_full.cmd
```

`run_full.cmd` performs three one-axis-at-a-time ladders around a shared baseline:

### Resolution ladder

```text
N = 32, 48, 64, 96
```

### Periodic image-shell ladder

```text
image_shell = 1, 2, 3
```

### Finite-difference ladder

```text
h/a = 3e-4, 1e-4, 3e-5, 1e-5
```

The common coarse grid is

```text
q = 2.31 .. 4.10
Delta q = 0.025
```

Every internally detected full-spectrum gap minimum or marginal-stability bracket is automatically rescanned at

```text
Delta q = 0.0025
```

No candidate location is supplied to the refinement code.

Identical baseline configurations appearing in more than one ladder are computed once and reused.

## Numerical convergence gates

For an isolated full-spectrum gap minimum to be promoted as a **converged numerical candidate**, v0.1.1 requires all of:

1. `|q*(N=64) - q*(N=96)| < 0.02`;
2. `|q*(image_shell=2) - q*(image_shell=3)| < 0.02`;
3. the same candidate cluster occurs for at least three finite-difference steps with total q-spread `< 0.02`.

Promotion means numerical convergence only. It does **not** assign any external physical meaning.

## Mode tracking

At every scan point the full Jacobian is diagonalized with eigenvectors. Consecutive eigenmodes are associated by maximizing

`|u_i(q_previous)^H u_j(q_current)|^2`.

Outputs include:

- `mode_min_overlap_prev`;
- `mode_median_overlap_prev`;
- `gap_mode_branch`;
- `gap_mode_overlap_prev`;
- full branch eigenvalues and overlap vectors in `mode_tracking`.

This makes it possible to distinguish a persistent mode branch from a gap minimum caused only by eigenvalue reordering.

## Roundoff floor gate

The neutral interaction diagnostic now records

```text
fd_roundoff_floor = eps_machine / (h/a)
neutral_signal_to_fd_floor = ||J_neutral|| / fd_roundoff_floor
```

A neutral-subspace event can nominate a candidate only when

```text
neutral_signal_to_fd_floor >= 100
```

The factor 100 is fixed in source, not a runtime tuning parameter.

## Outputs

`run_full.cmd` writes `audit_convergence/` containing:

- `independence_manifest.json`;
- one JSON result per ladder case;
- `convergence_rows.csv`;
- `candidate_clusters.json`;
- `audit_summary.json`.

A single scan still uses `run_blind_campaign.py` and additionally writes `mode_tracking.json`.

## Freeze before external comparison

After the campaign and before comparing to any outside model or target:

```bat
python freeze_results.py audit_convergence
```

This writes a SHA-256 manifest over the audit directory. Only after that freeze should external interpretation begin.

## Quick campaign

```bat
run_quick.cmd
```

The quick runner uses a reduced ladder and coarser q grid; it is a software/numerical sanity campaign, not the final convergence test.

## Dependencies

- Python 3.10+
- NumPy
- pybind11
- C++17 compiler

The hash-based native rebuild and pure-Python fallback from the C++/pybind audit template are retained.
