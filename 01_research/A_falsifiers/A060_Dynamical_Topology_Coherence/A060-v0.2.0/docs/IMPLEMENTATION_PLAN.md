# A060 v0.2.0 DEV - Cross-Paper Vortex Mechanics & Stability

**Date:** 2026-10-13. **Status:** DEVELOPMENT ANALYTICAL PREFLIGHT ONLY. **Intended framework:** `SST_Falsifier_Framework_v1.0.7` (`CANONICAL_FROZEN`, 2026-10-07). **Do not interpret any result in this package as a formal native FP64 scientific certification.**

## 1. Actual SST-Workbench audit, as viewed in Google Drive

- Existing family: `A060_Dynamical_Topology_Coherence/A060-v0.1.0`. Its current `project.json` sets `catalog_id=A060`, `version=v0.1.0`, `blind=true`, framework `v1.0.6`. Thus v0.2.0 must be an **additive successor**, preserving previous frozen scientific contracts, results and outputs. **Never replace the old A060.**
- Frozen template `SST_Falsifier_Framework_v1.0.7`: freeze file confirms `CANONICAL_FROZEN`; `PACKAGE_MANIFEST.json` reports 92 files. Validation report documents **56 passed**, with unchanged Python/C++/SYCL scientific backends relative to v1.0.6. Pinning is strict; explicit `SST_FALSIFIER_FRAMEWORK_ROOT` or `.sst_framework_root` wins and is fail-closed if invalid.
- `SST-Workbench/falsifier_registry.yaml` visible in a Workbench-root copy was modified **2026-09-25**, i.e. older than the A060 Oct-08 folder. It lists `A045_Two_Harmonic_Phase_Chirality_Floquet`; other Drive materials refer to `A045 Relative-Vorticity Triadic Geometry`. **Collision/mismatch unresolved**. It does not include the newer A054/A060. This older registry alone cannot authorize cross-family imports. Reconcile with the actual current canonical registry/branch before freezing.
- `A054-v0.5.1` exists in its own family folder; it remains a separate provider/state-selection branch. It contributes only an explicitly signed artifact contract after review. **No A054 verdict is imported in tranche M00--M04.**
- User's canonical Workbench location: `C:\workspace\projects\SST-Workbench`. New instance target: `01_research\A_falsifiers\A060_Dynamical_Topology_Coherence\A060-v0.2.0`. Keep `A060-v0.1.0` untouched.

## 2. Research scope and preregistration

**Physical basis:** three-dimensional, incompressible, inviscid Euler flow without external forcing. Viscoelastic, MHD, Gross-Pitaevskii, point-vortex gas and forced-Navier--Stokes results are not treated as SST-Euler validation. Landreman's MHD-equilibrium formulation is used only through its mathematically equivalent *steady-Euler* velocity/kinematic-pressure form.

**H0 (mechanical bridge):** exact algebraic and analytic controls are internally consistent but provide no evidence of dynamically stable, self-confined three-dimensional vortex knots, particle mass or long-range gravity. **H1 to be tested only in later phases:** a producer-qualified 3D Euler vortex geometry has reproducible dynamical stability and nonlocal pressure interaction exceeding matched null controls. Tranche M00--M04 **cannot** reject H0 about physical SST stability.

**Principle:** no particle labels, no tuned SST constants, no expected masses, no target-aware topology selection, and no reveal until the framework policy allows it. Missing upstream inputs remain `UNRESOLVED`, not `FAIL` or `PASS`. Run every computationally independent gate after a failure, unless data validity makes it unsafe.

## 3. Source lock, M00

Four primary analytic sources, SHA-256 values frozen in `sources/REFERENCE_HASHES.json`:

- P3 Chiarini, arXiv:2609.39826v1 - VA/VT projector and selective-VA dynamics;
- P4 Massey, arXiv:2609.32543v1 - shear cancellation wedge and rank-one/rank-two gates;
- P7 Landreman, arXiv:2609.26742v2 - exact steady 3D Euler toroidal fields;
- P9 Zhang and Yao, arXiv:2610.11029v1 - real-space scale flux identity and remainder.

Supplemental later-phase sources: Kerr (P1), Sabari/Tomio (P2), Kelvin-wave experiment (P8), vortex gas (P12). P5/P6/P10/P11 methodological only. No original papers are embedded in this code archive; configure `--source-dir` with owned PDFs at runtime.

M00 MUST fail closed at `SOURCE_HASH_MISMATCH`. Missing source -> `UNRESOLVED`. **Registry mismatch remains separately UNRESOLVED even if all PDFs match.** Sample local preflight status is not framework G0/G1 certification.

## 4. Analytic module M01: Landreman steady Euler

Reference at arbitrary `0<=epsilon<1`: `a=sqrt(1+epsilon)`, `b=sqrt(1-epsilon)`, `s=x^2/a^2+y^2/b^2`, `F=sqrt(1-(1-s)^2-4z^2)`,

```
B = ((2*z*x - (a/b)*F*y)/s,
     (2*z*y + (b/a)*F*x)/s,
      1-s)
Q_L = (x^2+y^2+4*z^2)/2
```

**Important transcription audit:** the division by `s` applies to the **whole numerator** of both horizontal components. A misread PDF linearization gave a non-solenoidal implementation; visual PDF verification corrected it. Inside the analytic toroidal domain (`F>0`, `s>0`), identities are

```
div B = 0
(B . grad)B + grad Q_L = 0
- tr((grad B)^2) = laplacian Q_L = 6
```

The pressure `Q_L` is **kinematic Euler pressure**; the MHD pressure is a distinct quantity. Dimensional physical scaling is `v=U0 B(x/L0)` and `p_E=rho_f U0^2 Q_L(x/L0)+const`, with no fixed SST constants used in the blind tests.

Preflight: 3 epsilon values `{0, 0.2, 0.5}` at one safe point using centered differences `h=1e-5`; thresholds divergence <3e-7, vector-momentum residual <2e-7, pressure-source residual <3e-6. Production: 3D interior sampling, symbolic/automatic differentiation independent of differences, `h` refinement, near-boundary exclusion/masks, and volume/pressure-surface checks.

## 5. Analytic module M02: Massey pressure silence

For trace-free `A=grad v`, let `S=(A+A^T)/2`, `omega=curl v`, `Q_A=-tr(A^2)/2`, `R_A=-det A`, `a2=||A||_F^2`, `f=1-sum(|eigenvalue(A)|^2)/a2`, `qhat=Q_A/a2`, `rhat=R_A/a2^(3/2)`, `m=max(2|qhat|,(2|rhat|)^(2/3))`, `chi=|omega^2/2-S:S|/a2`. Test:

```
2 Q_A = omega^2/2 - S:S
m <= 1-f <= 3m
```

Also test the stronger optimal ratio approx `2.0434311543` separately under an optimizer; no derived numerical threshold should be trained on later candidate geometry.

Exact controls: rank-one shear, rank-two nilpotent, balanced vortex with eigenvalues `a, a*exp(±2*pi*i/3)`, positive/negative rank-one gate `A12=g`, `A21=±epsilon`, rank-two closing gate `A12=A23=g`, `A31=epsilon`. Check pressure signs and eigenvalue splittings of orders `sqrt(g*epsilon)` and `(g^2*epsilon)^(1/3)`. For `A=0`, normalized invariants are **undefined**, not zero.

Preflight: 2,500 seeded independent trace-free random tensors; absolute wedge tolerance `1e-10`. This validates code/algebra, not turbulence or physical SST geometry. Later tests must use independent PKLSA-producer data, and conditional rank-one prevalence must be tested against matched Gaussian tensors, rather than assumed.

## 6. Analytic module M03: Chiarini VA/VT and projection

```
VA = (omega.S.omega)/|omega|^2 * omega
VT = (I-omega_hat omega_hat^T) S omega
S omega = VA + VT, omega.VT = 0
```

For the periodic modified-momentum force `laplacian g = curl VA`, the actual vorticity contribution is `curl g = -P_perp VA`, with `P_perp=I-grad inv_laplacian div`. The non-solenoidal remainder cannot in general be omitted from the local invariant equation. Harmonic/mean velocity modes require an explicit zero-mean convention.

Exact periodic control: `v=(sin y,sin z,sin x)` on `[0,2pi]^3`; spectral FFT reference, odd grid `N=25` to avoid Nyquist-realization issues. Expected: unprojected VA has nonzero divergence; projected force has small divergence; `curl g + P_perp VA` agrees to `1e-8`. Also test global `mean(omega.grad phi)=0` while local `omega.grad phi` is generally not zero. Physical correction: modified Chiarini dynamics is **not** canonical Euler, and nonconservation of kinetic energy due to the extra force must be accounted for.

Production: multiple odd/even resolutions, dealiasing, pointwise `omega=0` mask, spatial convergence and independent finite-difference implementation. Do not assert pointwise conservation of all vorticity moments under projected VA suppression.

## 7. Analytic module M04: Zhang-Yao spherical energy-flux identity

For a sphere of **diameter** `ell`, `I_ell=(2/5)(ell/2)^2=ell^2/10`. With trace-free filtered `A`, `S` and `omega` define `R_s=-tr(S^3)/3`, `V_s=omega.S.omega`, then the dipolar-gradient component is

```
Phi_ell^(L=1) = (ell^2/10) * (3 R_s + V_s/4)
Phi_ell = Phi_ell^(L=1) + O_ell
```

**Do not drop `O_ell` for nonlinear turbulent fields.** For a locally linear `u=A x`, the higher angular sectors vanish, so an independent spherical quadrature computes the same flux exactly from `delta u=ell A n`:

```
Phi_ell = -(3/(4ell)) * sphere_average(|delta u|^2 (delta u.n))
```

Reference controls include a balanced vortex with `Q_A=0`, `V_s=3a^3`, `R_s=-a^3/4`, and `3R_s+V_s/4=0`, plus randomized trace-free gradients. Preflight: 18 tensors, two-dimensional angular quadrature; tolerance 1e-12 relative. This is **not** a turbulence DNS or experimental validation of 90% flux capture.

Production: arbitrary smooth 3D Euler fields sampled over multiple filter scales, explicitly measuring the full residual `O_ell` and the L=3,5,... angular components, checking wall/periodic sphere handling, vector-component normalization, and cross-scale statistics. Compare against null gradient-only prediction instead of demanding an imported 90% score.

## 8. Two-level gate contract: M00--M04 versus framework G0--G9

Internal M modules are **subchecks**, not replacements for framework gate IDs. This mapping must be frozen in candidate `gate_map.json`:

| Framework v1.0.7 gate | Tranche use | Status until full instance |
|---|---|---|
| G0 | Protocol hash, pin and manifest check (M00) | UNRESOLVED until FREEZE |
| G1 | Independent source provenance, A045 registry reconciliation (M00) | UNRESOLVED |
| G2 | Analytic/numeric control suite (M01--M04) | DEVELOPMENT PRECHECK ONLY |
| G3 | Blind discovery (producer-qualified) | NOT YET RUN |
| G4 | Held-out confirmatory independent source | NOT YET RUN |
| G5 | Strict C++ FP64 certification | NOT YET RUN |
| G6 | SYCL/DD32 screening if enabled | NOT YET RUN |
| G7 | Independent replication groups | NOT YET RUN |
| G8 | Physical Euler stability mechanism | NOT YET RUN |
| G9 | Strict reveal commitment | NOT YET RUN |

The canonical `gate_plan.json` must retain framework schema `SST-GATE-PLAN-2`, and instance-specific frozen `science_contract.json`, `source_contract.json`, `falsifier.toml`, `blind_policy.json`, and `report/FALSIFIER_REPORT.tex` need to be generated/pinned inside a **new** v1.0.7 instance before `FREEZE`. The present source has no claim of official G0--G9 PASS.

## 9. Required full production regression additions

- R00: file SHA mismatch and missing source handling independently; stale-registry detection; no duplicate A060 version collision; no overwrite of v0.1.0.
- R01: Landreman incompressible/momentum/Poisson tests with exact/automatic gradient and grid/time/parameter sweep; pressure gauge invariance; invalid toroidal-domain rejection.
- R02: `A=0` handling, random tensor Wedge, sharp upper bound, extreme eigenvalue conditioning, rank-one/rank-two scaling slopes, full invariance under `SO(3)` rotations.
- R03: Fourier-Poisson zero mode and sign audit, Helmholtz projector parity, `omega=0` mask, `curl grad=0`, volume enstrophy consistency, explicit external-work budget.
- R04: direct spherical integration, longitudinal/transverse channels, filter radii versus diameters, angular-quadrature convergence, full `O_ell` residual from non-affine fields, forward/backscatter sign.
- R05: Python FP64/reference versus C++ FP64 native strictly same inputs, tolerances preregistered per observable, no automatic fallback. DD32/FP32 screening only.
- R06: reports, BLIND ZIP manifest/seals, nonce-based reveal logic, fail-close forbidden term scanner, stale output purge, PDF render and independent TeX/JSON consistency.

## 10. Instance generator and operational runbook

After verifying the user-authored canonical root and resolving the A045 family identity, generate the real instance **locally**:

```bat
cd /d C:\workspace\projects\SST-Workbench\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.7
py -3 tools\new_falsifier.py A060 cross_paper_vortex_mechanics ^
  C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A060_Dynamical_Topology_Coherence\A060-v0.2.0 ^
  --profile cpu --version v0.2.0
```

Copy only the **new scientific modules** into the generated instance's experiment/package code and tests; keep its bootstraps, launchers and framework implementation. Convert candidate M00--M04 scientific contracts into the exact framework schema. Do not copy the development `run_preflight.cmd` over the framework-generated `run_all.cmd`.

Then execute the canonical sequence:

```
run_all.cmd SELFTEST
run_all.cmd FREEZE
run_all.cmd BASIC
run_all.cmd FULL
run_all.cmd CERTIFY
run_all.cmd REVEAL_IF_ALLOWED
```

Set `SST_FALSIFIER_FRAMEWORK_ROOT` or rely on the generated `.sst_framework_root`, but never silently fallback to v1.0.6. If v1.0.7 native C++ is unavailable, G5 remains `UNRESOLVED` instead of being silently satisfied by Python results. **Freeze only after source/provenance reconciliation**, threshold review and a clean report validation.

## 11. Canonical outputs and PDF

Expected **formal framework** structure (not produced by this developer preflight):

```
A060-v0.2.0/
  .sst_framework_root
  science_contract.json
  source_contract.json
  gate_plan.json
  falsifier.toml
  blind_policy.json
  report/FALSIFIER_REPORT.tex
  <configured-name>_v0.2.0-outputs/
    GATE_LEDGER.json
    RUN_SUMMARY.json
    OUTPUT_MANIFEST.json
    REPORT_RENDER.json
    AUTO_RESULTS.tex
    reference/M00_sources.json
    reference/M01_landreman.json
    reference/M02_shear.json
    reference/M03_projection.json
    reference/M04_scale_flux.json
../<configured-name>_v0.2.0-outputs_BLIND.zip
../<configured-name>_v0.2.0-outputs_REVEALED.zip  # only after authorized reveal
../A060-v0.2.0_FALSIFIER_REPORT.pdf
```

The v1.0.7 report contract freezes the TeX protocol with science/source/gate/config/blind files and nonced private commitment. `AUTO_SCIENCE_CONTRACT.tex` and `AUTO_RESULTS.tex` are generated without modifying the frozen protocol. `POST_RUN_DISCUSSION.tex` is post-run only, outside the freeze. LaTeX compilation by `latexmk`/`pdflatex` must be checked via `REPORT_RENDER.json`. Never substitute this design-preview PDF for the official framework report or claim reveal occurred.

## 12. Planned handoffs to A045 and A054

- **A045:** Provide a read-only tensor diagnostic library interface with tensor convention `A_ij=partial_j u_i`, `Q_A`, `R_A`, `chi`, `f`, `m`, `r1`, `alpha_va`, `VT`, `R_s`, `V_s`, pressure-Poisson residual and explicit coordinate frame. Require explicit family-ID/provenance resolution first; never write into the A045 source.
- **A054 v0.5.1:** Only accept output from qualified 3D Euler/PKLSA producer with provider ID, geometry SHA-256, core type, `resolution_id`, perturbation cohort, and gate provenance. A058/A054-like phase/state-selection statuses remain independent; M01/M02 PASS never certifies a nucleon.
- **A060 parent v0.1.0:** Historical previous frozen contract untouched; avoid merging verdicts. v0.2.0 is a new experiment family version, NOT retrospective reclassification of the older run.

## 13. Observed development results, 2026-10-13

```
pytest: 6 passed
M00: REFERENCE_PASS - four uploaded PDF hashes matched (registry still UNRESOLVED)
M01: REFERENCE_PASS - max divergence 1.57e-10, max momentum residual 2.74e-10, max Poisson residual 3.37e-10
M02: REFERENCE_PASS - 2500 random tensors, max wedge violation 2.44e-15
M03: REFERENCE_PASS - projection curl error 3.44e-15; projected div 5.82e-14
M04: REFERENCE_PASS - 18 tensor flux tests, max relative discrepancy 4.55e-16
```

All are local analytic/numeric prechecks. They are not evidence of dynamical Euler-confinement, vorticity-materiality, gravity, particle masses, or valid physical parameter fits.

## References (abbreviated)

- Chiarini, A. (2026). *Is Vorticity Amplification Essential for Anomalous Dissipation and Intermittency in Turbulence?* arXiv:2609.39826v1.
- Massey, J. M. O. (2026). *Near-cancellation of enstrophy and strain requires shear or a balanced vortex.* arXiv:2609.32543v1.
- Landreman, M. (2026). *Analytic toroidal 3D MHD equilibria and steady Euler flows with invariant surfaces.* arXiv:2609.26742v2.
- Zhang, W. & Yao, H. (2026). *Geometric Mechanics of Real-Space Energy Transfer in Turbulence.* arXiv:2610.11029v1.
