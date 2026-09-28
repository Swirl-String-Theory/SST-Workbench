# SST Kelvin/Floquet Workbench — C006 v0.3.0

C++17/pybind11 + Python numerical workbench for target-blind Kelvin-wave, relative-periodic-orbit/Floquet, resonance, transfer, and spectral-certification tests in the SST vortex-filament research programme.

**v0.3.0 is a copy-on-write scientific extension of C006-v0.2.2.** K0–K14 retain their existing semantics. The new Phase V adds K15–K20, motivated by the numerical methodology in Batic & Dutykh (2026) without importing Gauss–Bonnet gravity, higher-dimensional black-hole dynamics, or quasinormal-mode boundary conditions into SST.

## Scientific hierarchy

The package keeps the following levels separate:

1. `PAPER_EQUATION_NUMERICAL_REPRODUCTION` — external benchmark equation reproduced numerically.
2. `REGULARIZED_BIOT_SAVART_*` — line-filament finite-core closure used for numerical falsification.
3. `FROZEN_LOCAL_KELVIN_SPECTRUM` — local Jacobian/eigenmode diagnostic around a specified geometry.
4. `TRUE_RELATIVE_FLOQUET` — allowed only after an accepted relative periodic orbit (RPO).
5. `FINITE_DIMENSIONAL_INTERTWINING_PRETEST_ONLY` — matrix diagnostic; not a Darboux proof.
6. `STRICT_SST_DARBOUX_ISOSPECTRALITY_GATE` — locked until SST supplies two derived scalar second-order operators with common domain and physical boundary conditions.

## Canonical SST scales

```text
v_swirl = 1.09384563e6 m s^-1
r_c     = 1.40897017e-15 m
Gamma_SST = 2*pi*r_c*v_swirl
          = 9.683619203488876e-9 m^2 s^-1
v_swirl/r_c = 7.763440655383073e20 s^-1
f0           = 1.2355899557047996e20 Hz
```

The C006 temporal generator uses

\[
\lambda = \sigma+i\omega,
\]

where \(\operatorname{Re}\lambda=\sigma\) is the local growth/decay rate and \(\operatorname{Im}\lambda=\omega\) is the oscillation frequency in the circulation-clock normalization. This is **not** the same complex-frequency convention as a black-hole QNM problem.

## Existing Phases I–IV: K0–K14

The v0.2.2 lineage remains intact:

- **K0–K3** — Rankine/Kelvin benchmark, SST scaling, native/Python parity, nonlinear ring amplitude sweep.
- **K4–K6** — ring spectrum, frozen trefoil spectrum, strict nonlinear RPO and true relative monodromy gate.
- **K7–K9** — blind four-/six-wave resonance search and coherence diagnostics.
- **K10–K14** — broadband transfer proxy, timescale separation, chirality audit, target-blind source scan.

The central rule remains:

> **No accepted RPO → no true Floquet monodromy.**

## New Phase V: K15–K20

### K15 — spectral persistence / stable-root tracking

The full four-eigenvalue projected Kelvin generator is recomputed over a pre-registered trefoil spatial-resolution ladder. Eigenvalues are matched in the complex plane with one-to-one Hungarian assignment and a scale-normalized shift

\[
d(\lambda_a,\lambda_b)=
\frac{|\lambda_a-\lambda_b|}
{\max(|\lambda_a|,|\lambda_b|,\epsilon)}.
\]

A branch is persistent only when every successive shift lies below the frozen tolerance. This adapts the paper's idea of retaining roots that persist under increasing spectral resolution, but it does **not** call C006 roots QNMs.

K15 also contains a generic quadratic-eigenvalue linearization self-test for

\[
\left(M_0+\lambda M_1+\lambda^2M_2\right)x=0.
\]

The QEP utility is implementation-ready for a future SST-derived second-order operator. It is not used to manufacture a quadratic formulation of the current first-order Kelvin generator.

### K16 — regularized-core continuation

The frozen-local spectrum is continued over a pre-registered \(\varepsilon/D\) grid. It records branch turning points and a descriptive non-oscillatory census. For the C006 generator a mode is called `overdamped_like` only when

\[
\frac{|\operatorname{Im}\lambda|}{|\lambda|}\leq \delta_{\rm osc}.
\]

This label is descriptive only. In an incompressible inviscid model it is **not** interpreted as viscous damping. The regularization length \(\varepsilon\) is not promoted to a derived SST core radius.

### K17 — spectral symmetry defect

For every frozen spectrum the code measures the nearest partners of

\[
\lambda^*,\qquad -\lambda,\qquad -\lambda^*.
\]

The gate is diagnostic. Exact Hamiltonian quartet symmetry is not assumed because the current four-mode projection need not preserve the full conservative operator structure.

### K18 — Darboux implementation self-test and SST intertwining pretest

A synthetic numerical pair

\[
A=\frac{d}{ds}+W(s),\qquad
A^\dagger=-\frac{d}{ds}+W(s),
\]
\[
H_+=AA^\dagger,\qquad H_-=A^\dagger A
\]

is used to verify the factorization/ispectrality implementation path.

Separately, the C006 common/differential 2×2 blocks are tested for approximate decoupling and for a finite-dimensional intertwiner \(X\):

\[
B X-X A\approx0.
\]

Even a passing matrix pretest would not establish a Darboux transformation of SST differential operators.

### K19 — strict SST Darboux gate

K19 is deliberately `SKIP` until all of the following exist independently of the desired result:

- two SST-derived scalar second-order operators;
- the same physical domain and matched boundary conditions;
- an explicit first-order intertwining/factorization relation;
- resolution-stable spectral agreement.

The scalar–vector Darboux result of Batic & Dutykh is therefore not transplanted into SST by analogy.

### K20 — local-spectrum ↔ true-Floquet cross-certification

Only when K6 has accepted an RPO and constructed the true relative monodromy does K20 compare local-generator predictions

\[
\mu_j^{\rm local}=\exp(\lambda_j T)
\]

with true monodromy multipliers \(\mu_j^{\rm Floquet}\). A Hungarian one-to-one match is used and the median normalized multiplier distance is reported. Agreement is a consistency test; it does not identify the two operators.

## Frozen v0.3.0 thresholds

`SPECTRAL_THRESHOLDS_FROZEN.json` was frozen before the first v0.3.0 Phase-V run. No fine-structure target, Gauss–Bonnet coupling, black-hole QNM frequency, or desired SST spectral value is encoded.

Quick preset:

```text
N ladder: 24, 32, 40
m = 1..3
eps/D: 0.08, 0.10, 0.12
stable-root relative shift <= 0.20
Darboux matrix pretest: coupling <= 0.05, spectrum <= 0.10, intertwiner <= 0.05
over-damped-like oscillation fraction <= 0.05
K20 median multiplier distance <= 0.25
```

Full preset:

```text
N ladder: 40, 56, 72, 88
m = 1..5
eps/D: 0.06, 0.08, 0.10, 0.12, 0.14
stable-root relative shift <= 0.12
```

## Commands

Normal Windows audit:

```bat
run_all.cmd
```

Higher-resolution campaign:

```bat
run_all.cmd full
```

Phase V only:

```bat
run_phase5.cmd
run_phase5.cmd full
```

Portable Python diagnostic without native build:

```bash
python run_phase5.py --preset quick --force-python --out-dir audit_out_phase5/phase5
```

The complete scientific run can also use the fallback backend:

```bash
python run_all.py --preset quick --force-python --out-dir audit_out_quick_python
```

## Phase-V outputs

```text
phase5/K15_trefoil_spectral_persistence.json
phase5/K16_core_parameter_spectral_scan.json
phase5/K17_conservative_spectral_symmetry.json
phase5/K18_darboux_intertwining_pretest.json
phase5/K19_strict_darboux_gate.json
phase5/K20_spectrum_true_floquet_crosscert.json
phase5/phase5_summary.json
```

## Interpretation limits

- No Gauss–Bonnet curvature term is introduced into SST.
- No higher-dimensional spacetime model is introduced into SST.
- The Batic–Dutykh black-hole boundary conditions are not reused.
- The current C006 Kelvin problem is not relabelled as a QNM problem.
- The current v0.3.0 physical spectrum is obtained from the projected finite-dimensional Kelvin generator, not a Chebyshev boundary-value discretization.
- The generic QEP solver and Darboux factorization are infrastructure for later derived SST operators; they are not evidence that such operators already exist.
- A negative real part of \(\lambda\) is not automatically viscosity in the inviscid SST interpretation.

See `docs/THEORY_AND_GATES.md` and `docs/BATIC_DUTYKH_2026_METHOD_BRIDGE.md` for the exact source-to-SST translation.

## References

```latex
\begin{thebibliography}{99}

\bibitem{BaticDutykh2026}
D.~Batic and D.~Dutykh,
``Quasinormal Modes of Gauss--Bonnet Black Holes via the Spectral Method:
Scalar, Vector, and Tensor Perturbations,''
arXiv:2608.06083 [gr-qc] (2026),
\url{https://arxiv.org/abs/2608.06083}.

\bibitem{Trefethen2000}
L.~N.~Trefethen,
\textit{Spectral Methods in MATLAB},
SIAM, Philadelphia (2000),
doi:10.1137/1.9780898719598.

\bibitem{TisseurMeerbergen2001}
F.~Tisseur and K.~Meerbergen,
``The Quadratic Eigenvalue Problem,''
\textit{SIAM Review} \textbf{43}, 235--286 (2001),
doi:10.1137/S0036144500381988.

\bibitem{Floquet1883}
G.~Floquet,
``Sur les equations differentielles lineaires a coefficients periodiques,''
\textit{Annales scientifiques de l'Ecole Normale Superieure}, Serie 2,
\textbf{12}, 47--88 (1883),
doi:10.24033/asens.220.

\end{thebibliography}
```
