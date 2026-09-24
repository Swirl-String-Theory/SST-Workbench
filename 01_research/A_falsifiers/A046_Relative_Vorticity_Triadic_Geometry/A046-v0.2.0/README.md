# A046 — Relative-Vorticity Triadic Geometry Blind Falsifier v0.2.0

v0.2.0 extends the v0.1.x structural result into a rotating-frame, delay-aware, three-layer blind falsifier.

The tested architecture is

\[
\boxed{
\mathbf u
\rightarrow
(\boldsymbol\omega_{\rm rel},S_{ij})
\rightarrow
\Phi_{\rm bulk}
}
\]

with two explicitly separate extensions:

\[
\boldsymbol\omega_{\rm abs}
=\boldsymbol\omega_{\rm rel}+2\boldsymbol\Omega_p,
\]

and

\[
M_\tau(t)=\Gamma(t)-\Gamma(t-\tau),
\qquad
\Delta\phi=\omega\tau.
\]

## What v0.2.0 tests

The release retains every v0.1.x gate and adds:

- exact reconstruction of the full local first-order velocity gradient from \(S_{ij}\) and
  \(\boldsymbol\omega\);
- absolute-vorticity consistency;
- north/south matched-cyclonic hemisphere symmetry in local tangent frames;
- \(\Omega_p\to0\) recovery of relative vorticity;
- SO(3) objectivity of the rotating-frame construction;
- a constant planetary-background no-curvature control for the exploratory metric;
- delay-phase recovery \(\Delta\phi=\omega\tau\);
- \(\tau\to0\) memory closure;
- a nontrivial finite-delay circulation-memory response.

The metric ansatz remains an exploratory diagnostic. Delay is **not** promoted into the metric in
this release.

## Blindness

Blind configuration and gates use dimensionless synthetic fields. They contain no canonical SST
constants, Newton's constant, fine-structure constant, particle masses, or Earth rotation rate.
Canonical SST values and the Earth rotating-frame benchmark enter only after the blind evidence tree
has been SHA-256 sealed.

## Provenance upgrade

The v0.1.x run established that the Windows C++/pybind11 backend builds and matches the Python
reference. v0.2.0 now makes that evidence part of the sealed release:

```text
BLIND/
  python_backend/
  native_backend/
  logs/
  runtime_python.json
  runtime_native.json
  backend_parity_summary.json
  prepare_manifest.json
  BLIND_SEAL_SHA256.txt
```

The native `.pyd` itself is not copied into the evidence package, but its exact path, byte size, and
SHA-256 are sealed in `runtime_native.json`.

## Run

Python reference only:

```bat
run_python.cmd
```

Full Python + C++17/pybind11/OpenMP qualification:

```bat
run_all.cmd
```

The full run performs Python campaign/tests, builds native, repeats the blind campaign through the
native backend, performs native tests and parity qualification, seals all blind evidence, reveals,
and packages the output ZIPs.

## Output identity

```text
A046_Relative_Vorticity_Triadic_Geometry_Falsifier_v0.2.0-outputs/
A046_Relative_Vorticity_Triadic_Geometry_Falsifier_v0.2.0-outputs_BLIND.zip
A046_Relative_Vorticity_Triadic_Geometry_Falsifier_v0.2.0-outputs_REVEALED.zip
A046_Relative_Vorticity_Triadic_Geometry_Falsifier_v0.2.0-outputs.zip
```

See `docs/HYPOTHESES.md`, `docs/V0.2.0_DYNAMIC_EXTENSION.md`, `docs/PROVENANCE_POLICY.md`,
and `docs/CANON_TRACE.md`.
