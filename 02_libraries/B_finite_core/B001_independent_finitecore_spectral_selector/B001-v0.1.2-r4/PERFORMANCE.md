# Performance notes — v0.1.2.4

v0.1.2.4 retains the v0.1.2.3 split between **quick/smoke performance** and **full/research reproducibility**.

## Safe optimizations used everywhere

1. The native/Python backend is loaded once per scan rather than once per q point.
2. The shell-0 self Jacobian is computed once per numerical case and reused for every q. It is independent of the periodic cell length by construction.

These changes leave the brute-force interaction Jacobian unchanged. In local native regression, the full/research path reproduced v0.1.2.1 candidate output exactly for an identical test grid.

## Quick-only C4 acceleration

`run_quick.cmd` additionally uses the exact quarter-turn symmetry of the cubic periodic image lattice when `N` is divisible by four. Only one representative quarter of Jacobian columns is evaluated and the remaining three quarters are reconstructed by a 90-degree index rotation.

An independently evaluated rotated-column audit remains active. The effective C4 gate uses the larger of:

- projected C4 leakage; and
- independent rotated-column audit error.

The C4 reconstruction is **not enabled by default for `run_full.cmd`**. Near-degenerate eigenvectors can change branch-tracking labels under matrix perturbations at ~1e-11 even when the global spectrum is unchanged. Therefore the research campaign retains the brute-force Jacobian for continuity with v0.1.2.1.

## Quick levels

### Fast smoke

```bat
run_quick.cmd
```

Defaults:

- base resolution `N=48`;
- resolution smoke ladder `N=32,48`;
- `dq=0.05`;
- `max_m=8`;
- quick-only C4 acceleration;
- duplicate configurations reused from memory.

This run is intended to verify the build, pipeline, Fourier decomposition, candidate plumbing and output schema. It is **not** a convergence result.

### Research quick

```bat
run_quick_research.cmd
```

Uses the same `N=32,48` quick ladder but restores:

- `dq=0.025`;
- `max_m=12`.

It is still not a replacement for `run_full.cmd`.

## Full research campaign

```bat
run_full.cmd
```

Retains the preregistered full ladders and brute-force interaction Jacobian. Only backend/self caching is applied by default.

## Disable quick C4 acceleration

For a direct quick comparison against the brute-force Jacobian:

```bat
run_quick.cmd --no-c4-accel
```


## Resume / restart

Completed case JSON files in the output directory are reused automatically when their normalized config, Fourier settings and acceleration mode match exactly. To force a clean recomputation:

```bat
run_full.cmd --no-resume
```

The same applies to quick runs.
