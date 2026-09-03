# SST Knot Geometry Library v0.1.0

Reusable **geometry-only** knot/filament seed library for SST falsifiers.

It is designed for the recent Trefoil Dynamic Seed Qualification, self-confinement/restoring-force, threaded-hole, finite-core and related blind campaigns. It does **not** implement fluid dynamics and it does not introduce free delay/feedback parameters.

## Why this library exists

The shader examples expose several useful mathematical constructions but mix them with rendering approximations. This package extracts the reusable geometry:

1. **Explicit trigonometric trefoil**
   \[
   \mathbf r(t)=s(\sin t+2\sin2t,\;\cos t-2\cos2t,\;-\sin3t).
   \]

2. **Anisotropic torus/track family**
   \[
   \mathbf X(t)=\mathbf U[R+a\cos(qt)]\cos(pt)
   +\mathbf V[R+a\cos(qt)]\sin(pt)
   +\mathbf N[b\sin(qt)+z_0].
   \]
   For \((p,q)=(2,3)\), this is a controllable trefoil seed. Independent `a` and `b` make radial bulge and axial weave separately sweepable.

3. **S3 lift / SO(4) rotation / stereographic projection** for topology-preserving geometric controls.

4. **Bishop / rotation-minimizing frames** for robust ribbons and material thread bundles without Frenet-frame failure at small curvature.

5. **Uniform arclength resampling + Fourier smoothing** for imported KnotPlot/Ridgerunner centerlines.

6. **Native geometry diagnostics**: approximate writhe, pairwise linking, curvature, nonlocal clearance, thickness proxy and resolution-convergence reports.

7. **Blind candidate campaign generator** with anonymous IDs and a SHA-256 reveal commitment.

## Important licensing/design note

No Shadertoy renderer or copyrighted shader source is redistributed here. The package is an independent implementation of the mathematical constructions: torus-knot parametrizations, stereographic projection, rotation-minimizing frames and polyline diagnostics. This keeps rendering code separate from falsifier geometry.

## Installation / Windows

Run:

```bat
run_all.cmd
```

This creates `.venv`, installs dependencies, builds the C++17/pybind11 backend, runs unit/reference tests, generates a seed suite, and creates a blind trefoil-track sweep.

Basic only:

```bat
run_basic.cmd
```

Custom blind campaign:

```bat
run_campaign.cmd configs\track_trefoil_seed_sweep.json outputs\my_campaign
```

## Core Python API

```python
import sst_knotlib as sk

# Shader-inspired anisotropic track trefoil
seed = sk.shader_track_trefoil(
    n=512,
    baseR=4.08248290463863,
    bulge_R=2.2,
    z_weave=3.0,
)

# Uniform arclength sampling
seed = sk.resample_closed(seed, 1024)

# Geometry qualification before dynamics
q = sk.qualify_seed(seed, core_radius=0.05, n=1024)
print(q)

# Six material threads in a Bishop frame
threads = sk.thread_bundle(seed, n_threads=6, turns=3.0, radius=0.12)
```

## Falsifier integration contract

A downstream falsifier should treat this library as a **pre-dynamics geometry layer**:

```text
raw/imported/analytic seed
        |
        v
uniform arclength resample
        |
        v
geometry qualification gates
  - sampling CV
  - curvature/core-radius
  - nonlocal clearance/core-radius
  - tube embeddability proxy
  - spatial convergence
        |
        v
blind ID + immutable geometry hash
        |
        v
existing Euler / finite-core / Biot-Savart / pressure / Floquet pipeline
```

The geometry stage should never inspect a later dynamic outcome when choosing or altering a seed.

## Recommended seed families for the latest trefoil qualification falsifier

### A. `track_trefoil`
Primary search family. Sweep

- `baseR`: overall major radius,
- `bulge_R = a`: radial lobe amplitude,
- `z_weave = b`: axial weaving amplitude,
- global scale after normalization.

The ratio

\[
\chi_{ab}=\frac{b}{a}
\]

is a useful shape coordinate: low values are flatter; high values are more axially woven.

### B. `classic_trefoil`
Independent analytic reference family.

### C. imported relaxed knots
Use `resample_closed()` and optionally `fourier_smooth()` before qualification.

### D. S3 controls
Use `s3_deform()` as a **nonphysical geometric null/control**. It preserves knot topology as long as the stereographic pole is not crossed, but can strongly alter Euclidean embedding metrics. Never interpret it as Euler evolution.

## Geometry gates

`qualify_seed()` currently reports:

\[
\kappa_{\max}r_c,
\qquad
\frac{d_{\min}}{r_c},
\qquad
\frac{\Delta_{\rm thick}}{r_c},
\qquad
CV(\Delta s),
\qquad
Wr.
\]

Default gates are deliberately configurable and dimensionless:

```text
clearance/core >= 2.2
max(kappa)*core <= 0.35
thickness_proxy/core > 1
segment CV <= 0.03
```

These are geometry qualification defaults, not SST physical laws.

## Native backend

`cpp/native.cpp` implements the expensive pairwise kernels using C++17/OpenMP:

- `min_nonlocal_distance`
- `writhe_midpoint`
- `linking_midpoint`

Python automatically falls back to NumPy/Python if the native module is unavailable.

## Numerical caution

The writhe/linking implementation uses a segment-midpoint Gauss quadrature. It is intended for ranking, convergence and regression testing. For publication-grade topological certification, require a resolution ladder and/or a dedicated exact/robust topology package.

## References

- R. L. Bishop (1975), *There is more than one way to frame a curve*, American Mathematical Monthly 82(3), 246–251. DOI: 10.2307/2319846.
- G. Calugareanu (1961), *Sur les classes d'isotopie des noeuds tridimensionnels et leurs invariants*, Czechoslovak Mathematical Journal 11, 588–625.
- J. H. White (1969), *Self-linking and the Gauss integral in higher dimensions*, American Journal of Mathematics 91(3), 693–728. DOI: 10.2307/2373348.
- F. B. Fuller (1971), *The writhing number of a space curve*, PNAS 68(4), 815–819. DOI: 10.1073/pnas.68.4.815.

## Python-only fallback

If a machine has no C++ build toolchain, use:

```bat
run_python_fallback.cmd
```

This validates the same API with the slower Python/NumPy pairwise kernels. For production falsifier campaigns, the native backend remains preferred.


## v0.1.3 provenance/runtime attestation
`prepare_for_falsifier()` now records the installed library version dynamically. `run_all.cmd` writes `outputs/runtime_validation.json` and requires both the native pybind11 backend and OpenMP.
