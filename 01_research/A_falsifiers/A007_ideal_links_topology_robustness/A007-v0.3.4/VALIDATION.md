# Validation — v0.3.4

## Automated tests

- `pytest`: **35 passed**.
- New tests cover analytic-Fourier spectral auditing, strict Nyquist guards, explicit cutoff guards, and FFT derivative exactness on resolved Fourier modes.

## Native parity

`run_native_audit.py --build-verbose` completed successfully.  The C++17/pybind11 source is unchanged from v0.3.3.  Representative absolute discrepancies remained at floating-point scale (about `1e-16` to `4.5e-16`).

## Four-link spectral audit

The source audit was run for `L6a4`, `L4a1`, `L6n1`, and `L7n2`.  All have source active mode 255 and therefore a strict Nyquist floor of 512 samples and a conservative nonlinear-geometry recommendation of 1024 samples.

| link | full-vs-m<=192 bending change | d2 power above 192 | precision-risk d2 fraction | combined tail/precision risk |
|---|---:|---:|---:|:---:|
| L6a4 (Borromean rings) | 39.69% | 49.70% | 0.831% | yes |
| L4a1 | 32.51% | 39.71% | 1.012% | yes |
| L6n1 | 35.31% | 44.22% | 2.349% | yes |
| L7n2 | 26.90% | 43.77% | 0.038% | no |

The combined risk flag is deliberately conservative and does **not** prove that high modes are spurious.  It reports that derivative-weighted high-mode sensitivity overlaps the assumed six-decimal coefficient-precision floor.

## Split continuum audit

A native full-preset audit was run for the same four links with analytic-Fourier geometry at `N=1024,2048,4096` and hydrodynamic/repulsion diagnostics at `N=512,1024`.

| link | geometry last-pair max | hydrodynamic last-pair max | N-continuum pass (5%) | v0.4 numerical-spectral ready |
|---|---:|---:|:---:|:---:|
| L6a4 | ~2.5e-14 | 2.014% | yes | no — source spectral precision risk |
| L4a1 | ~1.8e-14 | 1.972% | yes | no — source spectral precision risk |
| L6n1 | ~2.1e-14 | 2.336% | yes | no — source spectral precision risk |
| L7n2 | ~2.0e-12 | 3.142% | yes | yes under the configured v0.3.4 gate |

This separates the earlier false impression of bending non-convergence from the actual source-spectrum question.

## Claims boundary

- No physical Fourier cutoff is derived.
- `qm_*_spectral_filtered.json` presets are numerical regularization branches only.
- The source-precision risk assumes coefficient resolution `1e-6`; this is an audit assumption based on the supplied decimal coefficients, not a new CANON constant.
- No numerical Milnor `mu-bar_123` derivation is claimed for the Borromean rings.
- No QM claim is promoted solely from a filtered or spectrally unresolved branch.
