# A006 Blind Borromean & Swirl Clock Falsifier v0.1.0

**Status:** EXECUTABLE DEVELOPMENT DIAGNOSTIC. **NOT certified by the SST Falsifier Framework.**

This package contains a byte-for-byte copy of `A006-v0.5.0.zip`, an immutable source-frozen blind geometry loader, a genuine unforced multicomponent *regularized-filament* Biot–Savart integrator, matched twist-knot isolated / pair / triple / separated controls, balanced perturbation-growth measurements, feedback-response diagnostics, short-horizon frequency screening, source and run audit ledgers, native OpenMP acceleration, tests, and PDF report generation.

## Research question

Can initially unstable **individual** twist knots 5_2 and 6_1 display more bounded, less perturbation-sensitive motion when the *same initial filament geometries* are coupled as three-component candidate Borromean configurations? If yes, is there a reproducible **intrinsic collective oscillation** derived from those dynamics rather than prescribed by an SST time-dilation ansatz?

**Important:** individual instability has not been established independently by the included dataset. It is a *hypothesis tested*, not an assumed fact. `A006` describes components `5_2` and `6_1`; its three-component candidates have almost-zero pairwise Gauss-linking proxies, but **full Brunnian/Borromean isotopy, component knot types and Milnor triple invariant have not been certified**. These are not the classical three-unknot L6a4 Borromean rings. All source names remain masked in evaluator-facing analysis.

## Quick start (Windows, Python 3.10+, NumPy)

Unpack the ZIP to a sibling folder of A006. Source archive is already included in `sources/`; original A006 is **never changed**.

```cmd
py -m pip install -r requirements.txt
run_all.cmd SELFTEST
run_all.cmd PREPARE
run_all.cmd BASIC
run_all.cmd FULL --feedback --temporal-check
run_all.cmd REPORT
```

The `BASIC` scout is an inexpensive **unqualified** check: one source family per composition, chosen using sealed-source logic but without leaking composition into the evaluator. `FULL` tests six DEV geometry families (one N512/ORIG representation per family), three separated controls, finite perturbation stability, and does **not** certify the core resolution or clock merely by completing.

### Native acceleration (optional)

```cmd
build_native.cmd
run_all.cmd SELFTEST
```

`build_native.cmd` accepts MinGW `g++` or Visual Studio developer command prompt `cl`. When a native library is available it accelerates the same kernel with OpenMP (Open Multi-Processing) CPU parallelism; the Python/NumPy fallback works without it. Backend parity tests compare velocity fields. The included `.so` is Linux-only and never substitutes for building the Windows `.dll`.

### Higher-resolution, longer-horizon study

```cmd
run_all.cmd STABILITY --points 512 --steps 128 --horizon 1.0 --limit 2 --sector 0 --temporal-check
run_all.cmd FEEDBACK --points 256 --steps 64 --horizon 0.5 --limit 2
run_all.cmd MATRIX --points 256 --steps 64 --horizon 0.25 --sector 1 --limit 8
run_all.cmd REPORT
```

This can be **computationally intensive**: the Biot–Savart interactions scale approximately quadratically with total filament vertices. `--sector 0/1/2/3` are the preregistered circulation sign sectors `(+++), (++-), (+-+), (-++)`. Nothing is tuned to the canonical SST constants. A sufficiently large `--points` value **does not automatically qualify the simulation**; core separation, knot geometry, time/space convergence and topology remain independent gates. The high-resolution runs should be staged one geometrical family at a time, not all 48 DEV configurations at once.

### Blind holdout discipline

1. `PREPARE` produces `outputs/BLIND_INPUTS`, `outputs/BLIND_INDEX.json`, `outputs/SEALED_SOURCE_MAP.json`, source hashes and a split commitment. Only copy **BLIND_INPUTS**, **BLIND_INDEX**, code and preregistered science contract into an external evaluator workspace. Do **not** share the original ZIP or sealed source map with that evaluator.
2. `FULL` exercises DEV only. Review and pre-register any needed changes to the contract / algorithms before resetting a DEV study as a new version.
3. `LOCK` freezes implementation and contract checksums after a DEV `FULL` batch. It does **not** certify the science.
4. `HOLDOUT` is refused without a matching lock, and uses only the two sealed profile families reserved before execution.
5. `REVEAL` is refused unless holdout results exist; a `REVEAL_ONLY.json` source map is produced after the holdout run. Do not infer scientific certification from revealing.

```cmd
run_all.cmd LOCK
run_all.cmd HOLDOUT --points 512 --steps 128 --horizon 1.0 --temporal-check
run_all.cmd REVEAL
run_all.cmd REPORT
```

**Note:** Results of two resolutions or mirror images of the same profile/family never cross the DEV/holdout boundary. PREPARE cannot be repeated over a different source freeze.

## Outputs

- `outputs/SOURCE_FREEZE.json`, `SPLIT_COMMIT.json`, `BLIND_INDEX.json`
- `outputs/SEALED_SOURCE_MAP.json`: **restricted, do not share with blind evaluator**
- `outputs/BLIND_INPUTS/BX_*.npz`: normalized, unlabeled independent coordinate arrays
- `outputs/RESULTS/*_BASIC_SUMMARY.json`, `*_FULL_SUMMARY.json`, `*_STABILITY_SUMMARY.json`, `*_FEEDBACK_SUMMARY.json`, `*_MATRIX_SUMMARY.json`
- `outputs/RESULTS/*_FULL_###_BX_*.json`: measured per-component length, shape, curvature, clearance, perturbation amplification, optional response matrix, and unresolved science gates
- `outputs/DEV_LOCK.json` and `REVEAL_ONLY.json` only after explicit user-triggered stages
- `outputs/FALSIFIER_REPORT.md` and `outputs/FALSIFIER_REPORT.pdf` via `run_all.cmd REPORT`

All outputs label B0–B9 gates. A `NUMERICAL_FREQUENCY_CANDIDATE` is never a certified Swirl Clock. GPE (Gross–Pitaevskii equation) simulations and full three-dimensional Euler partial differential equation (PDE) have **not** been implemented in this instance. No reconnection, fluid-core internal torsion, Floquet multipliers, proper-time model or physics claim is inferred from the surrogate.

The included frozen paper explains GPE reconnection in a different physical model. The principal comparison is Guan, Zuccher & Liu (2025), *Physics of Fluids* **37**, 024126; DOI [10.1063/5.0252708](https://doi.org/10.1063/5.0252708).

## Verified status in this bundle

- Source archive SHA-256: `176da1ea176031952b499389eebc68cc150bb7ef378ebeb1c4cabd399d8bbd21`
- 64 prepared source-linked candidate geometries in 8 profile/composition families; 16 samples in two untouched holdout families.
- 18 automated regression tests, including a native versus NumPy velocity parity test, source tamper rejection, source-blindness checks, 3-arm controls and perturbation growth.
- Actual two-seed BASIC/FULL developmental runs are bundled; in both FULL runs the B2 core-resolution gate failed. **Do not interpret these as negative or positive evidence for physical stabilization.**

## Scientific limitations

1. **Topology**: no Milnor invariant/rigorous Brunnian certificate; source component knot labels from A006 are claims until verified. Rigidity of components does not imply a three-way Borromean link.
2. **Core**: the Rosenhead regularization is a model choice, not a measured finite-core vortex. Source knots have sharp turns and very close self-neighborhoods; critical convergence / nonlocal clearance gates may fail even at high vertex count.
3. **Stability**: finite deformation and finite-time amplification do not imply Lyapunov, nonlinear or orbital stability. `--horizon` is a numerical dimensionless time, not physical proper time.
4. **Feedback**: a nonzero off-diagonal response may be explained by pair interactions; no artificial restoring force or delayed-feedback term is inserted.
5. **Clock**: curvature-based frequencies cannot establish a local clock without independent phase signals and convergence. Intrinsic core torsion is absent from the centerline-only model.
6. **Framework**: this standalone development tool is **not** mislabelled as a frozen SST Falsifier Framework v1.0.10 instance. Transfer into that framework requires checking the actual locally installed framework contracts.

## Citations (copy-ready LaTeX)

```latex
\bibitem{Guan2025} H. Guan, S. Zuccher, and X. Liu (2025),
``Topological cascade of quantum Borromean rings,''
Physics of Fluids 37, 024126. doi:10.1063/5.0252708.
\bibitem{Saffman1992} P. G. Saffman (1992),
Vortex Dynamics, Cambridge University Press,
doi:10.1017/CBO9780511624063.
\bibitem{Milnor1954} J. Milnor (1954),
``Link Groups,'' Annals of Mathematics 59, 177--195,
doi:10.2307/1969685.
```
