# A056 PKLSA Spectral–Sine-Gordon–Mittag-Leffler Falsifier v0.1.0

## Scientific question

A056 asks two coupled but independently falsifiable questions about a phase field measured along a perturbed vortex carrier:

1. **Periodic phase-potential closure:** does the measured field obey a Sine–Gordon-type restoring law better than preregistered wave, linear Klein–Gordon, and cubic Duffing competitors?
2. **Fractional-memory ringdown:** after a perturbation, is the decay of a qualified modal/ringdown amplitude better predicted by a Mittag-Leffler relaxation than exponential, stretched-exponential, and bi-exponential alternatives?

The spectral theorem is used only as a mathematically valid analysis framework for self-adjoint covariance/POD operators. A056 does **not** claim to falsify the spectral theorem itself.

## Origin from the two supplied images

From image 1, A056 uses the two items that have a direct operational mapping to PKLSA data:

\[
A=\int_{\sigma(A)}\lambda\,dE_\lambda
\]

as the spectral/POD decomposition framework, and

\[
\varphi_{tt}-\varphi_{xx}+\sin\varphi=0
\]

as the prototype nonlinear phase equation. The implementation fits the dimensional generalized form

\[
\varphi_{tt}-c_\varphi^2\varphi_{ss}+\omega_0^2\sin\varphi=0,
\]

where \(s\) is arclength, \([c_\varphi]=\mathrm{m\,s^{-1}}\), and \([\omega_0]=\mathrm{s^{-1}}\) when SI coordinates are supplied.

From image 2, A056 uses the generalized Mittag-Leffler function

\[
E_{\alpha,\beta}(z)=\sum_{k=0}^{\infty}\frac{z^k}{\Gamma(\alpha k+\beta)}.
\]

The primary memory model is

\[
R_{\mathrm{ML}}(t)=E_{\alpha,1}\!\left[-\left(\frac{t}{\tau}\right)^\alpha\right],
\qquad 0<\alpha\le 1.
\]

The limit \(\alpha\to1\) recovers ordinary exponential relaxation:

\[
E_{1,1}(-t/\tau)=e^{-t/\tau}.
\]

The Laplace, Cauchy–Riemann, Pell/Fermat and contracted-Bianchi rows from image 1 are deliberately **not** forced into v0.1.0 because no unique PKLSA observable or admissible closure follows from those equations alone.

## Blind hypotheses

The phase lane compares

\[
\begin{aligned}
H_{\rm W}:&\quad \varphi_{tt}=a\varphi_{ss},\\
H_{\rm KG}:&\quad \varphi_{tt}=a\varphi_{ss}-b\varphi,\\
H_{\rm D}:&\quad \varphi_{tt}=a\varphi_{ss}-b\varphi-c\varphi^3,\\
H_{\rm SG}:&\quad \varphi_{tt}=a\varphi_{ss}-b\sin\varphi.
\end{aligned}
\]

For Sine–Gordon closure, A056 requires \(a>0\) and \(b>0\), plus predictive superiority on held-out time blocks.

The ringdown lane compares

\[
R_{\exp}(t)=e^{-t/\tau},
\]

\[
R_{\rm SE}(t)=e^{-(t/\tau)^\beta},
\]

\[
R_{\rm bi}(t)=w e^{-t/\tau_1}+(1-w)e^{-t/\tau_2},
\]

and \(R_{\rm ML}(t)\) above. A Mittag-Leffler claim is rejected if a finite ordinary modal/relaxation model predicts equally well or better.

## Gate order

`G0 provenance -> G1 admissibility -> G2 spectral qualification -> G3 phase-model competition -> G4 ringdown-model competition -> G5 independent replication -> G6 joint closure -> REVEAL`.

Each gate terminates in `PASS`, `FAIL`, `UNRESOLVED`, or `NOT_RUN_PREREQUISITE`.

### Primary thresholds

- G1: at least 24 time samples and 32 spatial samples; monotone finite grids; near-uniform sampling.
- G2: POD orthogonality residual \(<10^{-10}\); split-window top-mode subspace overlap \(\ge0.80\).
- G3: Sine–Gordon must have \(a>0,b>0\), design-matrix condition number \(\kappa_2\le10^8\), \(\Delta\mathrm{BIC}\ge10\) against the best competitor, and held-out NRMSE \(\le0.95\) of the best competitor.
- G4: Mittag-Leffler must have \(\Delta\mathrm{BIC}\ge10\), held-out NRMSE \(\le0.95\) of the best competitor, and fitted \(\alpha\) must lie away from the preregistered boundaries and below 0.97 so that it is distinguishable from the exponential limit.
- G5: at least two independent `source_group` values must reproduce the relevant support state. Meshes/seeds of one source group are not independent.
- G6: joint support requires both G3 and G4 support in at least two independent source groups; otherwise the result is partial, falsified, or unresolved as recorded in the ledger.

## Input contract

Each blind case is an `.npz` file containing:

- `t`: shape `(Nt,)`, strictly increasing;
- `s`: shape `(Ns,)`, strictly increasing;
- `phi`: shape `(Nt,Ns)`, phase in radians;
- optional `ringdown_t`: shape `(Nr,)`;
- optional `ringdown`: shape `(Nr,)`, a non-negative perturbation amplitude.

A sibling JSON file of the same stem contains public metadata:

```json
{
  "opaque_id": "C0001",
  "source_group": "independent-provider-id",
  "boundary": "periodic",
  "t_unit": "s",
  "s_unit": "m"
}
```

Topology names, particle labels, historical SST assignments and canonical SST constants belong outside the blind tree. `tools/convert_pklsa_npz.py` creates a conforming blind case while preserving a source SHA-256.

## Self-contained smoke campaign

`python tools/generate_smoke_data.py` regenerates five deterministic synthetic controls:

- Sine–Gordon + Mittag-Leffler;
- Sine–Gordon + bi-exponential;
- Klein–Gordon + Mittag-Leffler;
- Klein–Gordon + bi-exponential;
- a second independent Sine–Gordon + Mittag-Leffler positive control, exercising G5/G6 replication.

The control identities live only in `PRIVATE/smoke_reveal.json`; the blind files contain opaque IDs. Smoke results validate the falsifier implementation only and are **not SST evidence**.

## Run on Windows

```bat
run_all.cmd basic
```

For stricter numerical settings:

```bat
run_all.cmd full
```

Blind-only:

```bat
run_blind_only.cmd full
```

A real campaign can be run with:

```bat
run_real_blind.cmd D:\path\to\blind_cases full
```

The C++17/OpenMP/pybind11 extension is the preferred CPU kernel. Python remains the reference fallback and `run_10_selftest.cmd` checks parity when native code is available.

## Output convention

The run creates:

- `./A056_PKLSA_Spectral_SineGordon_MittagLeffler_Falsifier_v0.1.0-outputs/`;
- `../A056_PKLSA_Spectral_SineGordon_MittagLeffler_Falsifier_v0.1.0-outputs_BLIND.zip`;
- `../A056_PKLSA_Spectral_SineGordon_MittagLeffler_Falsifier_v0.1.0-outputs_REVEALED.zip`;
- `../A056_PKLSA_Spectral_SineGordon_MittagLeffler_Falsifier_v0.1.0-outputs.zip`.

## Interpretation boundary

A positive result would show that a preregistered reduced Sine–Gordon/fractional-memory description predicts qualified PKLSA observables better than the specified alternatives. It would **not** establish a Standard-Model particle assignment, quantum mechanics, gravity, or a unique microscopic mechanism. A negative result directly falsifies these two reduced closures for the tested carriers and perturbation regime.

See `PREREGISTRATION.md`, `EXPERIMENT_CONTRACT.md`, and `docs/REFERENCES.tex`.
