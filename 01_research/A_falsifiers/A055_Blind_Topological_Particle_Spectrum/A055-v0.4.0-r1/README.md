# A055 — Blind Topological Particle Spectrum Falsifier v0.4.0

A055 v0.4.0 is the **chiral-covariance follow-up** to v0.3.1 and remains a thin scientific instance of **SST Falsifier Framework v1.0.4 CANONICAL_FROZEN**.

## Why this is a major version

v0.3.1 removed the real-matrix conjugate-pair artifact and found many genuine signed traveling modes, but no frequency-matched bidirectional doublet. Its strongest new observation was a large one-way directional imbalance. Raw `+m/-m` direction, however, still depends on how an oriented filament is parameterized. v0.4.0 therefore asks a different question:

> Does a **circulation-relative**, representation-covariant directional bias survive gauge transformations, the full sealed spatial-resolution ladder, and both A054 Jacobian finite-difference steps?

## Primary observable

For component-resolved signed powers,

\[
\xi_{j,k}=\frac{\sum_c \operatorname{sgn}(\Gamma_c)(P_{jkc}^{+}-P_{jkc}^{-})}
{\sum_c(P_{jkc}^{+}+P_{jkc}^{-})}.
\]

Under the gauge-equivalent representation change

\[
C_c(s)\rightarrow C_c(-s),\qquad \Gamma_c\rightarrow-\Gamma_c,
\]

`+k` and `-k` exchange while the circulation sign also changes. A physical circulation-relative direction must therefore leave \(\xi\) invariant.

## Frozen controls

A mode is eligible when Kelvin fraction `>=0.50`, dominant-harmonic participation `>=0.50`, `|xi|>=0.60`, and `|Re(lambda)|/|Im(lambda)|<=1.0`. A sector needs at least **3** eligible modes and `|B_s|>=0.50`, where

\[
B_s=\frac{N_+-N_-}{N_++N_-}.
\]

A v0.4.0 robust anonymous candidate must keep the same circulation-relative bias sign:

- at every sealed A054 resolution (`N=56,72,88` in FULL),
- at both preregistered A054 Jacobian epsilon values,
- in at least **2** circulation sectors,
- while the metamorphic representation error stays `<=1e-8`.

Registered metamorphic controls are cyclic arclength-origin shifts, a deterministic rigid rotation, component permutation, and orientation reversal with circulation-sign reversal.

## Upstream policy

Production FULL requires already completed provenance-valid sources:

1. A054 v0.2.0-r2 sealed compound campaign;
2. A055 v0.3.1 framework output as the frozen discovery baseline.

v0.4.0 never launches upstream campaigns automatically.

## Run

```bat
run_all.cmd full C:\workspace\projects\SST-Workbench
```

## Interpretation boundary

A G8 PASS supports only a representation-covariant, resolution/epsilon-stable **linear chiral traveling-wave bias** in the finite projected filament model. It does not establish a particle identity, mass, charge, QCD state, or nonlinear confinement. The v0.3.1 source is discovery evidence from the same simulation family and is not independent confirmation.


## v0.4.0-r2 implementation note

This revision repairs runner plumbing only. The frozen v0.4.0 scientific protocol is unchanged. It restores the isolated A054 runner loader required by `compound_v040.py` and makes `run_all.cmd` propagate failures with a non-zero process exit code.

## r3 runtime maintenance

If an earlier v0.4.0/r1/r2 run failed either with false blind contamination inside `.venv/site-packages` or with `sealed=cpp_pybind11_openmp, actual=numpy_reference`, use the r3 release. The frozen v0.4.0 scientific protocol is unchanged; r3 only repairs runtime integration and packaging scope.


## r4 Windows long-path maintenance

The canonical sealed A054 runner may live below a path long enough that Windows refuses to load its `_native.pyd` with WinError 206 even though the file hash is correct. r4 does not alter that campaign. It verifies the source `RUNNER_MANIFEST.json`, copies the sealed runner byte-for-byte to a short temporary path, verifies the copy again, and imports the native extension from the short path. This is the same isolation strategy used by the original A054-v0.2.0-r2 native preflight. The frozen v0.4.0 scientific protocol is unchanged.
