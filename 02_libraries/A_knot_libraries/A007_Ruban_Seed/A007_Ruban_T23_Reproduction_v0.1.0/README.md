# Ruban T(2,3) Reproduction Falsifier v0.1.0

**Scientific status: `DEVELOPMENT_ONLY / RUBAN_REPRODUCTION_UNRESOLVED`.**

## Scope and rationale

Implements Ruban's *regularized Biot-Savart plus local induction* filament equation for the torus trefoil T(2,3), then tests whether the published long-lived B0=0.154 window can be reproduced. This is NOT the 3D incompressible Euler system, a physical finite-core model, an internal-twist model, or a background-vorticity lattice.

Ruban (2018) reports a quasi-stable T(2,3) example with **B0 = 0.154, Lambda = 1.4 + 0.5*ln(200) = 4.0491586833, delta/R0 = 1/20**, survival beyond t=300 and travel beyond 1200 R0. The paper does not publish full initial perturbation coefficients, detailed solver code, or a unique operational stop criterion; thus strict bitwise reproduction is impossible from the article alone.

The existing Google Drive E010 v0.4.0 atlas combines nominal and perturbed Ruban *geometry*, but explicitly marks `dynamic_stability=NOT_TESTED`; this package fills a **separate dynamics research gap**. No E010 files are changed. Original `3_1.xyz` and its geometrically modified variant are pinned in `inputs/` as provenance; the solver uses Ruban's direct analytic parameterization to avoid scaling/chirality ambiguities.

## Model (Ruban 1801.04822v2, Eq. 9)

We use dimensionless R0=1 and circulation Gamma=2*pi.

```text
X_t(beta) = 0.5 * integral_0^{2pi} [X_beta(beta') cross (X(beta)-X(beta'))]
                                      / (|X(beta)-X(beta')|^2+delta^2)^(3/2) d beta'
            + 0.5 * (Lambda + ln delta) * (X_beta cross X_beta_beta)/|X_beta|^3
```

The physical core width is **xi/R0 = exp(-Lambda) = 0.017437...** and is **not** delta=0.05. Both parameters enter the model via the compensating local induction. Initial trefoil (V_{1,2,3}):

```text
rho=1+B0*sin(3beta); X=rho*cos(2beta); Y=rho*sin(2beta); Z=B0*cos(3beta), beta in [0,2pi)
```

No extra internal twist is imposed; Ruban's line representation does not carry cross-section twist independently.

## Windows installation and execution

Python 3.11+ (Numba version must support the chosen NumPy version). From the extracted directory:

```bat
py -m pip install -r requirements.txt
run_all.cmd TEST
run_all.cmd SMOKE
run_all.cmd BASIC
run_all.cmd CONVERGE
run_all.cmd FULL
```

Linux/macOS: `python -m pip install -r requirements.txt; ./run_all.sh SMOKE`.

- `TEST`: regression tests only.
- `SMOKE`: N=64, dt=0.001, t=0.025; verifies finite field, ring symmetry, short-time invariants. **NOT a scientific stability result.**
- `BASIC`: N=128, dt=0.002, t=0.5, B0=[0.14,0.154,0.17]. Numerical screening only.
- `CONVERGE`: explicit short fixed-time *independent* N=64/128/256, dt/dt/2, delta=0.05/0.025 comparison. Output JSON, no automatic scientific promotion.
- `FULL`: N=256, dt=0.002, t=320, B0=[0.14,0.148,0.152,0.154,0.156,0.16,0.168]. **Computationally intensive; may stop early on numerical gates.**
- `CERTIFY`: same long duration at B0=[0.152,0.154,0.156], *does not automatically certify* until separate fixed-final-time multi-resolution and cross-method audits.

For a targeted run (recommended before all seven full cases):

```bat
py -m ruban_falsifier BASIC --n 256 --dt 0.001 --final-time 1.0 --snapshot-interval 0.1 --b0 0.154
py -m ruban_falsifier FULL --n 256 --dt 0.001 --final-time 320 --snapshot-interval 2 --b0 0.154
py -m ruban_falsifier.convergence --n 128 256 512 --dt 0.001 --final-time 1.0
```

No data are overwritten. Every run creates `./Ruban_T23_Reproduction_v0.1.0-outputs/` or a timestamp-suffixed sibling if occupied. A run places `FALSIFIER_REPORT.pdf`, `FALSIFIER_REPORT.md`, `gates.json`, `results.json`, `source_manifest.json`, traces, ring symmetry, and configuration inside its outputs. It also creates `../Ruban_T23_Reproduction_v0.1.0_outputs.zip` (relative to outputs directory) with SHA256 and `../Ruban_T23_Reproduction_v0.1.0_FALSIFIER_REPORT.pdf`. Source code hash and original seed SHA256 are recorded. The output ZIP is not a replacement for the source package.

## Hypotheses, gates, and stop rules

- H0: Ruban's regularized filament model has no distinct quasi-stability window at B0=0.154 under the reported parameters.
- H1: With adequately converged filament dynamics, a relative lifetime maximum in a narrow B0 window exists near 0.154.
- G0: provenance and geometric seed.
- G1: solver ring symmetry, finite velocity, direction.
- G2: numerical energy drift <= 1e-3 (pilot operating threshold); for article-grade comparison energy relative drift should approach ~5e-8 over T>300. These are different requirements.
- G3: target run t>300 and traveled axial distance >1200 R0 (Ruban's example), with no numerical stop.
- G4: compare neighboring B0 cases *at identical T* and resolved dt,N,delta.
- G5: spatial N, temporal dt, and regularization sensitivity at fixed physical/dimensionless final time, not mere visual persistence.
- G6: independent publication-figure agreement and original-method differences audited.
- G7: full Euler finite-core and internal-twist hypotheses explicitly `NOT_TESTED`.

Operational stops: relative energy drift >1e-3; polygon adjacent-segment ratio >10; aligned shape RMS >0.25 R0; nonfinite or degenerate geometry. Ruban's publication does not provide a fully specified stop rule, so these **operational choices must not be compared one-to-one with his lifetime graph**. A simulated topological crossing is not a reconnection; no reconnection algorithm exists in this model. Filament coalescence must be detected separately before topological conclusions.

## Initial observed results, 30 Oct 2026

| Pilot | Result | Interpretation |
|---|---|---|
| N=64, dt=0.001, t=0.025, B0=0.154 | relative energy drift 2.07e-6 | early solver sanity |
| N=128, dt=0.002, t=0.5, B0=0.140 | 5.37e-5 | short-time numerical gate pass |
| N=128, dt=0.002, t=0.5, B0=0.154 | 8.38e-4 | short-time numerical gate pass, marginal |
| N=128, dt=0.002, B0=0.170 | numerical energy stop at t=0.2 (1.72e-3) | unqualified, not physical knot failure |
| N=256, dt=0.001, t=1.0, B0=0.154 | 1.90e-5 | best initial pilot, NOT Ruban >300 |

An independent short t=0.03 N=64/128 dt/dt/2 test found temporal shape differences ~5e-10 but spatial differences ~0.004 R0, indicating **spatial convergence still not established**; delta variation also changes shapes. These values have no independent SST experimental meaning.

## Source provenance and reproducibility

- Ruban arXiv:1801.04822v2 and arXiv:1806.10783v2: model and initial geometry.
- E010 v0.4.0 (Google Drive): combined geometry-only source; not imported into dynamics under original provider identity.
- `inputs/user_3_1.xyz`: original user-supplied 1024-point knot; SHA256: `38d7ebfb37dc381da081bc13b0bc763b422775e78b4a8d90e4d727eedb161871`.
- `inputs/user_ruban_B0154_paper.xyz`: geometry-only preparation from the prior turn; separate from Ruban's analytic seed.

**Framework status:** standalone execution with a framework-compatible reporting/gate *concept*, but not a certified direct integration with the SST Falsifier Framework v1.1.0 RC2. The catalog ID is left unassigned to avoid collision. Integrate through the local family hierarchy and registry with versioned manifests and admission checks before promoting.

## References - copy-ready LaTeX

```latex
\bibitem{Ruban2018Letters}
V. P. Ruban (2018),
``Long-Lived Quantum Vortex Knots,''
JETP Letters 107, 307--310.
\url{https://doi.org/10.1134/S0021364018050120}

\bibitem{Ruban2018JETP}
V. P. Ruban (2018),
``Quasi-Stable Configurations of Torus Vortex Knots and Links,''
Journal of Experimental and Theoretical Physics 127, 581--586.
\url{https://doi.org/10.1134/S106377611809008X}
```
