# A045 — Relative-Vorticity Triadic Geometry Blind Falsifier v0.1.0

Purpose: test whether the local first-order basis
\[
\{\mathbf u,\boldsymbol{\omega},S_{ij}\}
\]
is structurally better suited than
\[
\{H,\boldsymbol{\omega},\Gamma\}
\]
for an SST-style clock/transport/spatial-response layer, while preserving the
CANON-v0.8.36 separation between local pressure/optical response and the
nonlocal Poisson/bulk response.

This is a **structural falsifier**. It does not claim that the exploratory
metric ansatz is physical gravity, and a passing run is not evidence for SST gravity.

## Canon-v0.8.36 interfaces used

The design is anchored to the current Canon interfaces:

- local clock/optical factor:
  \[
  S_{(t)}=\sqrt{1-\|\mathbf u\|^2/c^2},\qquad n_\gamma=S_{(t)}^{-1},
  \]
- passive Euler locking:
  \[
  \delta p_{\rm swirl}=-\frac12\rho_f\|\mathbf u\|^2,\qquad
  \delta n_\gamma \simeq -\frac{\delta p_{\rm swirl}}{\rho_f c^2},
  \]
- stress / bulk projection:
  \[
  \mathbf f_{\rm grav}=\rho_m\mathbf g+\nabla\!\cdot\boldsymbol{\sigma}_{\rm swirl},
  \]
- weak coarse Poisson response:
  \[
  \nabla^2\Phi=4\pi G_{\rm eff}\rho_{\rm eff},
  \]
- organized-transport research route:
  \[
  \nabla^2\Phi_{\rm org}\propto\partial_i\partial_j(u_i u_j).
  \]

The Canon's triadic response corollary is treated as a diagnostic separation
of response channels; this falsifier does not reinterpret those channels as
three coordinates.

## Main hypotheses

1. **HWC local-completeness falsifier**  
   Helicity, vorticity, and circulation are not a locally complete basis.
   Two incompressible flows are constructed with identical local velocity,
   vorticity, helicity, and loop circulation, but different strain.

2. **UWS local discriminability**  
   The candidate basis \(\{\mathbf u,\boldsymbol{\omega},S_{ij}\}\) must
   distinguish that pair.

3. **Clock-pressure locking guard**  
   On a steady Beltrami/ABC Euler control, the exact clock/pressure
   elimination identity is tested without SST numerical constants.

4. **Poisson nonlocality gate**  
   A localized divergence-free vortex generates
   \(Q=\partial_i\partial_j(u_i u_j)\); the spectral Poisson solve must
   reproduce \(Q\) and yield a field extending outside the strongest-source
   region.

5. **Exploratory metric consistency**  
   A preregistered weak metric ansatz constructed from speed, vorticity,
   and strain must remain Lorentzian, give zero numerical curvature for a
   constant-flow null control, nonzero curvature for a nonuniform control,
   and satisfy Riemann pair symmetry numerically.

6. **Objectivity**  
   Scalar invariants and the pointwise tensor construction must be invariant
   or covariant under a rigid SO(3) rotation.

## Blindness discipline

`run_blind.py` uses only dimensionless synthetic flow fields and preregistered
tolerances. It contains **no** values of \(\rho_f\), \(r_c\),
\(\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}\), \(G\), \(\alpha\), or
particle masses.

Only `reveal.py` imports `sst_triadic/reveal_constants.py`.

## Run

Python reference:

```bat
run_python.cmd
```

Full native workflow:

```bat
run_all.cmd
```

Output:

```text
../../SST_Relative_Vorticity_Triadic_Geometry_Falsifier_v0.1.0-outputs/
```

See `docs/HYPOTHESES.md`, `docs/CANON_TRACE.md`, and
`docs/BLIND_PROTOCOL.md`.
