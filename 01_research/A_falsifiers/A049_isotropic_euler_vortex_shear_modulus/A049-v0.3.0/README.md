# A049 — Isotropic Euler-Vortex Shear-Modulus Falsifier v0.3.0

Research question:

\[
\boxed{\text{Can an isotropic Euler-vortex microstructure generate a nonzero, conservative transverse shear modulus?}}
\]

v0.3.0 replaces the v0.2.0 random spectral background by an explicit **topologically persistent finite-core vortex-filament microstructure**. The blind candidate consists of an approximately isotropic ensemble of identical Hopf-linked two-loop microcells evolved by regularized Biot–Savart dynamics.

The release asks four progressively stronger questions:

1. Does the explicit linked geometry have positive affine shear curvature \(\mu/\rho>0\)?
2. Does that curvature and the corresponding odd shear stress persist under conservative vortex evolution?
3. Is the response approximately direction-independent, objective, reversible, and topology-preserving?
4. Does the resulting conditional transverse speed close the preregistered Master-Factor target
   \[
   c_T/v_*=1/2,
   \qquad v_*=\Gamma/(2\pi a)?
   \]

An unlinked geometrically matched control is included. Therefore v0.3.0 can distinguish **vortex-line stiffness** from a specifically **linking-induced** stiffness.

## Model

Each closed filament obeys a regularized Biot–Savart advection law. The blind Hamiltonian-like kinetic energy per fluid density is

\[
\frac{E}{\rho}
=\frac{1}{8\pi}
\sum_{ij}
\frac{\Gamma_i\Gamma_j\,d\mathbf l_i\!\cdot d\mathbf l_j}
{\sqrt{|\mathbf r_i-\mathbf r_j|^2+a^2}}.
\]

The effective shear modulus is measured directly from the second derivative of this energy under volume-preserving affine shear. A separately sheared \(+\gamma\)/\(-\gamma\) ensemble is evolved to measure stress relaxation rather than inferring persistence from a static Born curvature alone.

## Blindness

The blind configuration contains no \(\alpha\), \(c\), \(r_c\), \(\rho_{\!f}\), canonical SST swirl speed, or canonical SST circulation. Reveal maps \(a\to r_c\) only after the full blind evidence tree is SHA-256 sealed.

## Scope guard

This is a **regularized vortex-filament microcell model**, not a proof for the full 3D Euler PDE and not yet a connected continuum vortex network. A positive result qualifies this specific topological microstructure. A bulk Maxwell-like wave additionally requires an independently observed transverse pole; v0.3.0 does not infer one from a modulus alone.

## Run

Python reference campaign:

```bat
run_python.cmd
```

Python + C++17/pybind11/OpenMP qualification:

```bat
run_all.cmd
```
