# SST Trefoil Dynamic Seed Qualification Mega Falsifier v0.3.3

## Purpose

v0.3.3 is the corrective **periodic-cubic operator-split arclength-remap** release built from v0.3.2 after the remap-kernel audit found that the implementation used polygonal linear interpolation rather than the preregistered periodic-cubic map.
It addresses the v0.3.1 observation that continuous tangential mesh controllers can alter the discretized embedded centreline.

The new numerical map separates

1. physical finite-core vortex-filament evolution, integrated by RK4; and
2. a discrete uniform-arclength remap performed at frozen physical times.

No tangential mesh velocity is added to any RK4 stage in S37C/S40/S50/Phase B.

## Gate hierarchy

```text
S20 -> S30 -> S32 -> S35
   -> S37A legacy continuous-mesh gate (historical comparator)
   -> S37B legacy diagnostic-only closure
   -> S37C NEW operator-split remap certification  [S40 admission]
   -> S40 long operator-split dynamics
   -> S50 projected Floquet replay of the same frozen map
   -> S60 -> Phase B -> reveal
```

S37C compares several remap intervals on the same physical RK4 plan at each resolution.  The no-remap trajectory is retained as a diagnostic reference but is not an admission arm because it may lose marker quality even when the embedded physical curve remains meaningful.

## Target-free trefoil shape ratio

Every operator-split trajectory also records

\[
\chi_{\rm eff}(t)=\frac{R_{\rm radial}(t)}{r_{\rm axial}(t)}.
\]

The amplitudes are extracted intrinsically from the ordered centreline using a PCA torus axis and the trefoil's \(T(2,3)\) toroidal/poloidal Fourier structure.  `chi_eff` is **diagnostic only**: it is absent from candidate scores, thresholds and promotion logic.  No target ratio is supplied to discovery.

## One-click Windows runs

```bat
run_all.cmd
run_all_extended.cmd
run_all_production.cmd
```

A scientific run requires an explicit held-out trefoil-atlas path:

```bat
run_all.cmd C:\path\to\held_out_trefoil_atlas
```

The historical `KnotPlot\knots\final` directory may still be used for diagnostics, but v0.3.1 already established that it can fail the independent-source-diversity requirement; v0.3.2 therefore does not silently default to it.

The package keeps the v0.3.1 output-security convention. BASIC results live under:

```text
./SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier_v0.3.3-outputs/basic/
```

`run_all.cmd` first creates the shareable blind archive, then performs explicit S70 reveal, then creates the revealed archive:

```text
../SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier_v0.3.3-outputs_BLIND.zip
../SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier_v0.3.3-outputs_REVEALED.zip
```


## Remap-kernel audit / diagnostic

Before spending a held-out atlas on S37C, run the target-free numerical diagnostic:

```bat
run_03_remap_kernel_benchmark.cmd --smoke
```

The smoke uses the analytic \(T(2,3)\) curve only and cannot promote a scientific candidate. The full benchmark (omit `--smoke`) uses a longer horizon and is intended for the native backend. The actual scientific gate remains `run_37c_operator_split.cmd` after S35 has produced core-robust blind candidates.

## Scientific scope

This release tests numerical closure of a regularized vortex-filament surrogate.  It does not establish full 3D Euler stability, a stable physical trefoil vortex, SST, or a fundamental geometric constant.
