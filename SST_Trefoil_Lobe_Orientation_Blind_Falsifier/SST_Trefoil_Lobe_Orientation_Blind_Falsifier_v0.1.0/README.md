# SST Trefoil Lobe-Orientation Blind Falsifier v0.1.0

A ready-to-run blind test of the hypothesis that the three mutually tilted lobes of a trefoil generate an orientation-dependent **non-local finite-core Biot–Savart response** that can stabilize intrinsic shape modes or separate the closest cross-lobe approach.

## Default datasets

The CMD scripts require no dataset arguments when these files exist:

```text
C:\workspace\projects\SST-Workbench\KnotPlot\Knots_FourierSeries\3_1\knot.3_1.fseries
C:\workspace\projects\SST-Workbench\KnotPlot\knots\final\knot_3.1_final.txt
```

The Fremlin parser evaluates the finite Fourier coordinate series and both inputs are uniformly resampled by arclength, centered, and normalized to identical total length `2*pi` before blinding.

## One-command run

```bat
run_all.cmd
```

This performs installation, native build, smoke tests, BASIC and EXTENDED campaigns.

For a faster first look:

```bat
run_basic.cmd
```

For CPU/OpenMP extended:

```bat
run_cpu.cmd
```

For Intel Arc / oneAPI SYCL:

```bat
run_gpu_sycl.cmd
```

## What is actually tested

1. `B01/B02` source blinding before scoring.
2. Three-lobe detection independent of source identity.
3. Six reduced perturbation modes: three tilt + three breathing.
4. Symmetric `+eps/-eps` finite differences at several epsilon values.
5. Exact native velocity decomposition: local / same-lobe / cross-lobe / transition.
6. Rigid translation, rigid rotation and tangential reparameterization removal.
7. Reduced Jacobian and eigenvalues.
8. Closest cross-lobe separation/approach rate.
9. Deterministic matched orientation-scrambled controls.
10. Nonlinear finite-amplitude ringdown with **no reconnection operator**.
11. Perfect circular unknot null control for artificial radial collapse.
12. EXTENDED only: periodic-box pressure-Poisson diagnostic.

The detailed preregistration is in `docs/PREREGISTRATION.md`.

## Important physical interpretation

This package does **not** assume a hard core repulsive force. The regularized kernel only gives a finite core scale. If `d_min` enters the preregistered near-core threshold, the run reports a `core_event`; it does not bounce, reconnect, cut, splice or add a penalty force.

A positive closest-pair `cross_lobe` distance rate means the cross-lobe induced velocity is separating at that instant. It is not automatically a Newtonian pair force.

The reduced Jacobian is used because ideal vortex-filament dynamics is first order; a stable restoring mode can be oscillatory and need not appear as a simple negative scalar slope in the same coordinate.

## SST dimensional mapping

Normalized calculations use `Gamma=1` and total centerline length `2*pi`. By default the core radius is calibrated **blindly per geometry** as 90% of a robust tube-thickness estimate, then that normalized radius is mapped to the fixed SST physical core `r_c`. This avoids choosing a different physical core for Fremlin and KnotPlot while allowing their geometric ropelengths to differ. The report maps these to SST using

```text
Gamma_SST = 2*pi*r_c*v_swirl
ell_0     = r_c / a_core
T_0       = ell_0^2 / Gamma_SST
V_0       = Gamma_SST / ell_0
p_0       = rho_f * V_0^2
```

with the canonical constants included in the config.

## Main outputs

```text
00_preregistered_config.json
backend_info.json
pre_unblind/B01_analysis.json
pre_unblind/B01_score.json
pre_unblind/B02_analysis.json
pre_unblind/B02_score.json
pre_unblind/blind_verdict.json
unblind_manifest.json
final_verdict.json
summary_metrics.csv
REPORT.md
plots/*.png
```

`pre_unblind/blind_verdict.json` is the key artifact for auditing that the scientific score existed before source identities were restored.
