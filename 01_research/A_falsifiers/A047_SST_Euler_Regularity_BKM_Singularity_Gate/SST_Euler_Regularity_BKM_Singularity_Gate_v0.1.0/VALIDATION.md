# Validation — SST Euler Regularity / BKM Singularity Gate v0.1.0

Date: 2026-09-11

## Build / self-tests

Native backend was compiled in the execution container from `cpp/native.cpp` using C++17 and pybind11 headers available locally. The standard package remains configured for pybind11 via `pyproject.toml`/`setup.py`.

Self-tests: **3/3 passed**.

1. native T(2,3) trefoil-vorticity seed shape/finite-value test;
2. Fourier Leray projection divergence test;
3. ABC Beltrami-flow rotational-Euler RHS test (`u x omega = 0` after projection).

## BASIC blind campaign

Six dimensionless runs completed. All six passed the preregistered numerical-validity gates.

| revealed condition | N | dt | max omega growth | relative energy drift | max RMS div(u) | candidate |
|---|---:|---:|---:|---:|---:|---|
| baseline_N24 | 24 | 0.0030 | 1.0157790502 | 1.674e-11 | 2.240e-16 | no |
| baseline_N32 | 32 | 0.0030 | 1.0047002678 | 1.799e-11 | 2.719e-16 | no |
| baseline_N40 | 40 | 0.0030 | 1.0025063712 | 1.832e-11 | 2.468e-16 | no |
| baseline_N32_dt_half | 32 | 0.0015 | 1.0047002679 | 1.950e-12 | 3.071e-16 | no |
| adversarial_packet_N32 | 32 | 0.0030 | 1.0000000000 | 1.192e-11 | 2.866e-16 | no |
| adversarial_packet_N32_dt_half | 32 | 0.0015 | 1.0002632188 | 2.183e-12 | 3.352e-16 | no |

Blind verdict:

`NO_CONVERGED_BKM_CANDIDATE_IN_WINDOW`

Candidate runs: **0/6**.

## Convergence diagnostics

- N=32 baseline time-step halving changes the vorticity-growth observable by `4.20e-11` relatively.
- N=32 -> N=40 baseline spatial change in the vorticity-growth observable is `2.188e-3` (0.219%).
- Packet N=32 time-step halving changes the vorticity-growth observable by `2.631e-4` (0.0263%).
- Energy conservation and solenoidal projection are substantially tighter than the frozen gates.

## Scientific interpretation

This result is **not evidence that 3-D Euler is globally regular**, and is not a numerical contradiction of the 2026 finite-time blow-up construction. It establishes only that this short-window, smooth synthetic trefoil-tube family and the first strain-aligned packet proxy do not display the preregistered resolution-consistent BKM-candidate signature.

The N=24 -> N=32 -> N=40 decrease in apparent max-vorticity growth indicates that part of the coarse-grid growth is resolution-sensitive. The N=32 time-step pair is essentially temporally converged for the baseline observable over the tested window.

## Execution note

The initial six-run process was interrupted by the host execution wall-time after four completed baseline cases. The two missing adversarial cases were resumed with the identical frozen configuration; completed baseline outputs were not recomputed. The final blind assessment was generated only after all six case summaries existed.
