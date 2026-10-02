# Wien–Planck SST Field–Matter Closure Falsifier v0.3.0

## PTSA / dynamic-carrier release

v0.3.0 is a major dataset and methodology change. The primary discovery population is no longer the external KnotPlot `final` directory. It is the **self-contained SST Parametric Trefoil Seed Atlas v1.0.0 (PTSA)** bundled under `datasets/`.

PTSA is the canonical name for the 48-candidate analytic family previously described informally as the *shader-derived set*. The name describes the mathematics, not the rendering platform that inspired the extraction. No Shadertoy renderer/SDF/source code is bundled.

The 48-candidate grid is generated from

\[
\mathbf X(t)=\mathbf U[R+a\cos(3t)]\cos(2t)
+\mathbf V[R+a\cos(3t)]\sin(2t)
+\mathbf N[b\sin(3t)+z_0],
\]

with 3 values of `R`, 4 of radial bulge `a`, and 4 of axial weave `b`. Candidate filenames are parameter-opaque hashes. The full independent generator is preserved in the tiny bundled `vendor/SST_Knot_Library_v0.2.5.zip`.

## Scientific chain

```text
PTSA 48 analytic candidates
 -> geometry/hash inventory
 -> STRICT DIMENSIONLESS seed qualification
      rolling coherence + short shape survival + mesh quality
 -> preregistered top-N promotion
 -> matched -eps / +eps action campaign
 -> automatic observation-window extension if FFT peak is window limited
 -> POD frozen discovery/holdout mode
 -> dimensionless energy/action gates
 -> blind archive
 -> manual reveal
```

A later stage cannot rescue a failed seed-qualification or recurrence prerequisite. A peak in the first non-zero FFT bin is marked `frequency_window_limited` and is not accepted as an intrinsic mode.

## Strict blindness

The pre-reveal scientific path uses only dimensionless `L_hat=1`, `Gamma_hat=1`, core fraction, geometry and numerical controls. It does not consume SST canonical constants, SI scales, `h`, or `hbar`. The absolute normalization audit remains reveal-only.

## One-click Windows run

```bat
run_all.cmd
```

No dataset argument is required. The package is self-contained.

Optional external historical control:

```bat
run_reference_knotplot_final.cmd "C:\workspace\projects\SST-Workbench\KnotPlot\knots\final"
```

KnotPlot `final` is a reference/control population in v0.3.0, not the primary discovery set.

## Output convention

All results go to

```text
./Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.3.0-outputs/
```

and the blind run automatically creates

```text
../Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.3.0-outputs.zip
../Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.3.0-outputs_BLIND.zip
```

Both are blind-safe. Private reveal keys stay under `private_reveal_keys/` and are never included. After explicit reveal:

```bat
run_40_reveal.cmd
```

v0.3.0 creates

```text
../Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.3.0-outputs_REVEALED.zip
```

The reveal also resolves opaque PTSA filenames back to the preregistered `(R,a,b)` parameters and writes `REVEALED_PTSA_SELECTION.json`. The default `Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.3.0-outputs.zip` deliberately remains blind-safe.

## Bundled dataset footprint

The atlas is deliberately small: 48 × 512-point XYZ centerlines plus manifests. The reusable generator library is only ~79 kB compressed. This makes a self-contained falsifier substantially below typical multi-megabyte result archives.

## Important interpretation

PTSA geometry is a search space, not evidence that a preferred SST particle shape has already been found. `T(2,3)` is an expected construction label. Dynamic qualification chooses carriers without looking at the Universal Action outcome. Discrete frequencies are not action quantization; the amplitude-continuity null remains mandatory.
