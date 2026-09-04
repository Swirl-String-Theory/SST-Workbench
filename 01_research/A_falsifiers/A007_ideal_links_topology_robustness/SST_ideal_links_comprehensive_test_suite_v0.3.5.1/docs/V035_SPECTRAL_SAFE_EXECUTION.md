# v0.3.5 — Spectral-safe QM execution and v0.4 bridge

## Bug fixed

v0.3.4 had a control-flow/configuration defect: raw `qm_full` used `N=96` even when the source had active
Fourier mode 255. The code correctly blocked readiness afterwards, but still computed and wrote a full
sub-Nyquist Hessian first. That output could look physical despite being numerically rejected.

v0.3.5 moves the spectral guard **before** native hydrodynamic/Hessian work.

## No silent geometry changes

A raw source is never silently low-pass filtered. The user must choose one of:

- fixed raw sampling: reject if insufficient;
- `auto-nonlinear`: preserve coefficients and raise N explicitly;
- explicit cutoff config: Research Track numerical regularization.

## Matched cutoff ladder

The v0.4 bridge compares full-central Hessians at:

- m<=64, N=384;
- m<=96, N=512;
- m<=128, N=768.

All three use the same reduced mode order (`mode_max=2`) and the same closure settings. The ladder tests
relative-equilibrium and gradient changes, negative Hessian mode counts, symplectic rank, unstable linear-mode
counts, and finite-difference step convergence.

A cutoff-stability PASS is a numerical robustness result only. It is not evidence that any Fourier cutoff is a
physical SST law.
