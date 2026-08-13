# SST Maxwell-Inspiration Falsifier v0.1.0

This package implements seven preregisterable falsification/audit routes inspired by J. Clerk Maxwell's *On Faraday's Lines of Force* (1855--1856), while explicitly **excluding** the inadmissible direct identification "Maxwell's resisting-fluid $1/r$ pressure = SST gravity".

The package is designed for SST's incompressible, inviscid material Euler sector and keeps it separate from the independent transverse/link field $\mathbf A_{\rm eff}$ used in the Canon radiation sector.

## Seven tests

| ID | Maxwell-inspired route | What is actually tested | Failure means |
|---|---|---|---|
| T01 | $\mathbf v$ as a material "swirl-tonic" vorticity potential | $\boldsymbol\zeta=\nabla\times\mathbf v$, $\nabla\cdot\mathbf v=0$, and Stokes consistency by independent line/surface quadratures | the numerical/material field realization is inconsistent with the claimed vorticity-potential structure |
| T02 | circulation as topological holonomy | $\oint_C\mathbf v\cdot d\boldsymbol\ell \simeq \sum_i\Gamma_i\,Lk(C,\gamma_i)$ and orientation/sign controls | circulation is not locked to the declared topological flux sector at convergence |
| T03 | moving-loop / relative-motion induction identity | $d\Gamma_C/dt=\oint_C[(\mathbf v-\mathbf u_C)\times\boldsymbol\zeta]\cdot d\boldsymbol\ell$ | the resolved ideal-Euler transport law fails after discretization error is removed |
| T04 | exterior harmonic/Hodge sector | exterior curl/divergence residuals, recovered circulation coefficient, and reduced $\nabla\phi+\Gamma\mathbf h_K$ reconstruction | the exterior field is not explained by the claimed harmonic circulation sector plus a curl-free gradient nuisance sector |
| T05 | energy--helicity stationarity | Beltrami positive control plus optional centerline test of $\delta E=\lambda\,\delta H$ | the tested state is not stationary under the proposed energy-at-fixed-helicity closure |
| T06 | cyclic-work / chirality response | symmetry of quasistatic response Jacobian and $\oint \mathbf F\cdot d\mathbf q$ over closed cycles | a passive quasistatic constitutive law would yield non-zero cyclic work; the closure is incomplete or non-conservative |
| T07 | derived radial force-flux | radial coherence, shell flux plateau, and fitted decay exponent of a declared candidate acceleration field | the declared candidate does not generate a Newtonian-like $r^{-2}$ exterior sector |

T07 includes a compact-vortex Bernoulli-pressure **negative control**. For a localized compact filament the direct Biot--Savart velocity has no Newtonian monopole. The negative control is therefore expected to reject the $r^{-2}$ gate.

## Quick start

Windows:

```bat
run_all.cmd
```

PowerShell:

```powershell
./run_all.ps1
```

Portable:

```bash
python -m maxwell_sst.cli demo --out outputs
```

The run writes `summary.json`, `summary.csv`, and per-test JSON files.

## Analyze a KnotPlot/Ridgerunner centerline

Supported single-component formats are `.vect`, `.csv`, `.txt`, `.npy`, and `.npz`.

```bash
python -m maxwell_sst.cli centerline path/to/3_1.vect --out outputs_3_1 --gamma 9.68361920e-9 --core-a 0.05
```

`--core-a` is in **the same coordinate units as the centerline**. It is a numerical regularization/core scale, not automatically the Canon horn/circulation radius $r_c$.

For normalized knot geometry, the absolute energy scale is not meaningful unless a physical length mapping and density are supplied. T05 therefore uses normalized stationarity residuals by default.

## Native acceleration (optional)

A small pybind11/CMake module is supplied for high-resolution Biot--Savart, Gauss-linking, and regularized filament-energy kernels. The Python implementation is always available as fallback.

```bat
build_native.cmd
```

or

```bash
cmake -S native -B native/build
cmake --build native/build --config Release
```

The native module is optional; all validation tests run without it.

## Canon patch

`CANON_PATCH/SST_CANON-v0.8.35_to_v0.8.36_Maxwell_swirl_tonic.patch` is intentionally based on **SST_CANON-v0.8.35.tex**. It adds a material swirl-tonic/vorticity-potential subsection immediately after Circulation Quantization, without identifying the material velocity field with the Canon's independent photon/link field $\mathbf A_{\rm eff}$.

The patch also adds a Maxwell provenance citation and v0.8.36 edition note. A standalone insertion block is provided in `CANON_PATCH/01_material_swirl_tonic_block.tex`.

## Epistemic interpretation

Passing T01--T04 validates identities/representations and the numerical realization; it does not prove an electromagnetic ontology. T05--T07 are stronger model discriminators. In particular, failure of T05 falsifies only the tested energy--helicity closure, and failure of T07 falsifies only the declared candidate for a radial gravity-like flux, not all possible SST gravity closures.

## Canonical numerical scales used only where dimensionally appropriate

- $\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}=1.09384563\times10^6\ \mathrm{m\,s^{-1}}$
- $r_c=1.40897017\times10^{-15}\ \mathrm m$
- $\Gamma_0=2\pi r_c\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}=9.68361920\times10^{-9}\ \mathrm{m^2\,s^{-1}}$

The v0.8.35 Canon treats the historical $7.0\times10^{-7}\ \mathrm{kg\,m^{-3}}$ value as a legacy/reference normalization rather than a closed primitive material density. The package therefore names it `RHO_REF` and does not silently promote it to an independently derived $\rho_f$.
