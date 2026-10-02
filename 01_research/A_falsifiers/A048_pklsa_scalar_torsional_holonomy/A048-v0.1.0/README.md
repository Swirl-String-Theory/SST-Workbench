# A048 — PKLSA Scalar–Torsional Holonomy Blind Falsifier v0.1.0

This release is the first executable qualification scaffold for the SST/PKLSA hypothesis that a closed finite-core vortex tube may possess an internal material-phase/torsional branch distinguishable from conventional Kelvin bending dynamics.

The key discriminant is dispersion:

\[
\omega_K(k) \propto k^2
\]

for a Kelvin/LIA-like null branch versus

\[
\omega_\chi^2(k)=c_\chi^2 k^2+\Omega_0^2
\]

for a candidate scalar/torsional phase branch. A separate geometric forward model uses PKLSA centerline curvature and torsion, but **v0.1.0 does not treat that model as evidence**.

## Scientific status

v0.1.0 performs **instrument qualification**, not a physical confirmation of SST. It tests whether the analysis can reliably distinguish linear/gapped from quadratic dispersion under blinded synthetic labels, verifies gauge/holonomy invariants, validates geometry numerics, and provides a fail-closed PKLSA trefoil adapter.

A physical SST gate requires dynamical observations produced independently of the candidate torsional PDE (for example finite-core Biot–Savart/Euler evolution or an experiment). Without such observations, a simulated torsional wave only tests the simulator.

## PKLSA contract

The adapter targets the current trefoil contract:

```text
SST_Parametric_Knot_Link_Seed_Atlas_v0.1.1/
  manifests/CANDIDATES_FULL.jsonl   (or .csv)
  families/14_knot_3p1.npz
```

Expected bundle shape: `(48, 1, 512, 3)`.
Scientific ingest can enforce SHA-256:

```text
ffc31331fccaf10a3171e4ccbf3ec0043e56ff681f85cc8b8149932193d736d1
```

## Blind/reveal separation

The blind stage contains no canonical SST constants. Anonymous synthetic case labels are generated at runtime and committed by SHA-256. The label map remains outside the evidence tree until `reveal.py` verifies the blind seal.

After reveal, the canonical SST scale mapping reports

\[
\Gamma_c=2\pi r_c\mathbf{v}_{\!\boldsymbol{\circlearrowleft}},\qquad
\beta_c=\frac{\Gamma_c}{4\pi}=\frac{r_c\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}}{2},\qquad
 t_c=\frac{r_c}{\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}}.
\]

## Run

Python reference qualification:

```bat
run_python.cmd
```

Full Python + C++17/pybind11 qualification:

```bat
run_all.cmd
```

Optional PKLSA geometry screen:

```bat
python pklsa_preview.py "C:\path\to\SST_Parametric_Knot_Link_Seed_Atlas_v0.1.1"
```

## Output identity

```text
A048_PKLSA_Scalar_Torsional_Holonomy_Falsifier_v0.1.0-outputs/
A048_PKLSA_Scalar_Torsional_Holonomy_Falsifier_v0.1.0-outputs_BLIND.zip
A048_PKLSA_Scalar_Torsional_Holonomy_Falsifier_v0.1.0-outputs_REVEALED.zip
A048_PKLSA_Scalar_Torsional_Holonomy_Falsifier_v0.1.0-outputs.zip
```

## Source separation

`docs/SOURCE_TRANSLATION.md` distinguishes what is actually present in the 2014 notebook from the modern fluid-mechanical and PKLSA formulation added here.
