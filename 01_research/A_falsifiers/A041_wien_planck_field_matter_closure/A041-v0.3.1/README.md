# Wien–Planck SST Field–Matter Closure Falsifier v0.3.1

## Scientific-certification correction after the first PTSA run

v0.3.1 keeps the self-contained **SST Parametric Trefoil Seed Atlas v1.0.0 (PTSA)** introduced in v0.3.0, but corrects four methodological weaknesses exposed by the first blind PTSA campaign:

1. first-bin/sub-cycle frequency estimates are now resolved by an **iterative multi-cycle horizon certification loop**, not by a single extension;
2. the centerline relative-equilibrium gate is now **normal/gauge projected**, while the full material-marker residual is retained separately;
3. long trajectories use **adaptive arclength reparameterization** and a dynamic substep budget;
4. action energy and mode frequency are measured on the **same frozen, independently discovered normal mode**.

The fifth correction is coverage accounting: every preregistered carrier/resolution/amplitude slot now produces either an `OK` row or an explicit error row, and the blind scorer has a dedicated complete-coverage gate.

The package remains SST-constant-blind and SI-blind before reveal.

## Primary geometry population

The default dataset is the bundled PTSA:

```text
datasets/SST_Parametric_Trefoil_Seed_Atlas_v1.0.0/
```

It contains 48 analytic trefoil candidates generated from

\[
\mathbf X(t)=\mathbf U[R+a\cos(3t)]\cos(2t)
+\mathbf V[R+a\cos(3t)]\sin(2t)
+\mathbf N[b\sin(3t)+z_0].
\]

The grid contains 3 values of `R`, 4 values of radial bulge `a`, and 4 values of axial weave `b`. Candidate filenames are parameter-opaque. The reveal-only manifest maps them back to the preregistered parameters. No Shadertoy renderer, SDF, or shader source is redistributed; only an independent mathematical implementation and the generated centerlines are included.

The exact reusable generator/provenance dependency remains bundled as:

```text
vendor/SST_Knot_Library_v0.2.5.zip
```

## v0.3.1 scientific chain

```text
PTSA 48 analytic candidates
        |
        v
geometry/hash inventory
        |
        v
STRICT DIMENSIONLESS seed qualification
  - normal rolling coherence
  - short free-dynamics shape survival
  - adaptive mesh-quality control
        |
        v
preregistered top-N promotion
        |
        v
dedicated broadband discovery probe
        |
        v
POD mode discovery
        |
        v
normal-bundle projection + RMS normalization
        |
        v
FROZEN mode
        |
        +--> matched +/-A mode energy
        |      Delta E_hat_phi(A)
        |
        +--> matched +/-A mode dynamics
               frequency of the same phi
        |
        v
iterative frequency-horizon certification
        |
        v
fixed-horizon temporal convergence
        |
        v
blind Universal-Action gates
        |
        v
BLIND archive
        |
        v
manual reveal only
```

The relevant blind observables are therefore

\[
\Delta\hat E_\phi(A)
=\frac{\hat E(X_0+A\phi)+\hat E(X_0-A\phi)}{2}-\hat E(X_0),
\]

\[
\hat J_{f,\phi}=\frac{\Delta\hat E_\phi}{\hat f_\phi},
\qquad
\hat J_{\omega,\phi}=\frac{\Delta\hat E_\phi}{\hat\omega_\phi}.
\]

The energy and frequency now refer to the same frozen mode by construction.

## Iterative frequency certification

A first non-zero FFT bin is never accepted as an intrinsic frequency. If the matched-mode spectrum is window limited or contains too few cycles, v0.3.1 increases the **dimensionless** horizon and reruns the same frozen-mode experiment:

\[
T_0\rightarrow T_1\rightarrow T_2\rightarrow\cdots
\]

until the preregistered cycle requirement is met or a fixed horizon/round cap is reached. No target value, SST constant, or SI time scale is consulted. BASIC defaults to a maximum factor of 32 and six extension rounds.

If the cap is reached without resolving the mode, the row is labeled `UNRESOLVED_HORIZON_CAP` and recurrence-dependent gates fail or become `SKIP_PREREQUISITE`.

## Gauge-projected relative equilibrium

For an unlabelled centerline, tangential marker motion is a parametrization degree of freedom. v0.3.1 therefore separates two diagnostics.

Full material-marker residual:

\[
\epsilon_{\rm RE}^{\rm full}
=\frac{\|\mathbf u-\mathbf u_{\rm rigid}\|}{\|\mathbf u\|}.
\]

Centerline/normal residual:

\[
\epsilon_{\rm RE}^{\perp}
=\frac{\|P_\perp(\mathbf u-\mathbf u_{\rm rigid})\|}
       {\|P_\perp\mathbf u\|}.
\]

The blind centerline gate uses `epsilon_RE_perp`. `epsilon_RE_full` remains reported for later material-labelled finite-core studies.

## Adaptive mesh-gauge control

The solver still uses RK4 with

\[
\Delta\hat t
\propto
(\Delta\hat s_{\min})^2,
\]

but long trajectories no longer rely on a fixed small number of reparameterization events. A preregistered mesh trigger causes uniform-arclength redistribution when the spacing CV or edge ratio becomes too large. The solver records:

- maximum mesh CV observed before redistribution;
- maximum edge ratio observed;
- sample-time mesh quality;
- number of adaptive reparameterizations;
- dynamic substep budget and actual step count.

The scientific mesh gate uses the **maximum observed pre-redistribution** diagnostics, so adaptive cleanup cannot hide a hard mesh excursion.

## Complete-coverage gate

Expected campaign size is fixed before scoring:

\[
N_{\rm expected}
=N_{\rm carriers}\,N_{\rm resolutions}\,N_{\rm amplitudes}.
\]

Every slot must exist and have `row_status=OK`. Missing or failed numerical rows make

```text
UA0b_complete_campaign_coverage = FAIL
```

and downstream action claims cannot pass.

## Strict blindness

Before reveal, the scientific path uses only

\[
L_{\rm hat}=1,
\qquad
\Gamma_{\rm hat}=1,
\]

dimensionless geometry, core fraction, perturbation amplitudes, and numerical controls. It does not use canonical SST values, SI conversion scales, `h`, `hbar`, or a target action.

The blind source/config/payload guard is run before the campaign and again before scoring.

## One-click Windows run

BASIC:

```bat
run_all.cmd
```

EXTENDED:

```bat
run_all_extended.cmd
```

HIGHRES:

```bat
run_all_highres.cmd
```

The production configs keep `require_native=true`; the C++17/pybind11 backend must therefore build successfully before the scientific run proceeds.

The external historical KnotPlot population remains available only as a control:

```bat
run_reference_knotplot_final.cmd "C:\workspace\projects\SST-Workbench\KnotPlot\knots\final"
```

## Output convention

All results are written under

```text
./Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.3.1-outputs/
```

The blind chain automatically creates

```text
../Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.3.1-outputs.zip
../Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.3.1-outputs_BLIND.zip
```

Both are blind-safe. Private reveal keys remain outside the output tree under `private_reveal_keys/`.

Only after explicit reveal:

```bat
run_40_reveal.cmd
```

is the separate archive produced:

```text
../Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.3.1-outputs_REVEALED.zip
```

The default `-outputs.zip` remains blind-safe even after reveal.

## Interpretation boundary

A blind PASS can establish only a **dimensionless numerical universal-action candidate** in this regularized centerline model. It cannot by itself establish Planck quantization, an absolute SI action, a preferred SST particle geometry, topology certification, a true Floquet spectrum, or full three-dimensional finite-core Euler stability.

Absolute comparison with `h` or `hbar` remains reveal-only and requires an independently sourced dimensional normalization.
