# SST Ideal Links Comprehensive Test Suite v0.2.1

This release builds on the v0.2.0 C++17/pybind11 audit architecture with thickness-admissibility gates and corrected nonlocal self-contact / arclength-weighted geometry diagnostics.

The preregistered set is:

`L2a1 L4a1 L5a1 L6a1 L6a2 L6a3 L6a4 L6a5 L6n1 L7a1 L7a2 L7a3 L7a4 L7a5 L7a6 L7a7 L7n1 L7n2`

The bundled `idealLinks.txt` contains 130 ideal links from 2–9 crossings; the same campaign can be extended to the complete database.

## Native production path

The expensive kernels are implemented in `cpp/native.cpp` and exposed as
`sst_link_suite.native_ext._native`:

- batched, multi-component Rosenhead–Moore Biot–Savart velocity;
- every circulation-sign sector in one C++ call;
- Gauss-linking matrix;
- regularized Neumann coupling matrices;
- OpenMP parallelization where the compiler supports it.

For component signs \(\sigma_i\in\{-1,+1\}\), the native code evaluates

\[
\mathbf u(\mathbf x)
=
\sum_i \frac{\sigma_i}{4\pi}
\sum_k
\frac{
\Delta\boldsymbol\ell_{ik}\times(\mathbf x-\mathbf m_{ik})
}{
\left(\lVert\mathbf x-\mathbf m_{ik}\rVert^2+\epsilon^2\right)^{3/2}
}.
\]

The Python/NumPy implementation remains an independent reference backend, not merely a wrapper around C++.

## Hard native gate

`--require-native` enforces all of the following before a campaign starts:

1. the extension builds and imports;
2. C++ and Python velocities agree for representative 2- and 3-component links;
3. the Gauss-linking matrices agree;
4. the Neumann coupling matrices agree;
5. no silent Python fallback occurs.

Absolute or relative parity is accepted only within the tolerances stored in the selected JSON preset. The complete ledger is written to `native_audit.json`.

## Build and test

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
py -3 -m pip install -e ".[test]"
py -3 -m sst_link_suite.cli build-native --force --strict
py -3 -m pytest
py -3 run_native_audit.py --force-build
```

On Windows, the builder first uses the installed C++ toolchain through setuptools/MSVC. On Linux/macOS it attempts a direct C++17 build and retries without OpenMP if necessary. A source hash prevents stale binary reuse.

## Campaign commands

Fast strict-native validation:

```powershell
py -3 scripts/run_all.py --preset quick --require-native
```

Full 18-link campaign:

```powershell
py -3 scripts/run_all.py --preset full --require-native
```

Maximum campaign:

```powershell
py -3 scripts/run_all.py --preset max --require-native
```

All 130 supplied links:

```powershell
py -3 scripts/run_all.py --preset full --all-database --require-native
```

Explicit Python reference run:

```powershell
py -3 scripts/run_all.py --preset quick --force-python
```

The top-level `run_all.cmd` and `run_all.ps1` require native execution by default.

## Analysis matrix

### Source and Fourier gates

The reconstruction convention is

\[
\mathbf r(t)=\frac{\mathbf A_0}{2}+
\sum_{n\ge 1}\left[\mathbf A_n\cos(nt)+\mathbf B_n\sin(nt)\right].
\]

The suite checks closure through the third derivative, declared versus integrated length, coefficient power, spectral entropy and Fourier-tail sensitivity.

### Geometry

Per component:

- centerline length and standard radius-based ropelength;
- curvature, torsion and high quantiles;
- total curvature and \(\int\kappa^2\,ds\);
- inertia eigenvalues, planarity, axisymmetry and area vector;
- component-length imbalance.

Gilbert uses diameter normalization \(D=1\). Therefore

\[
\operatorname{Rop}_{\rm standard}=\frac{L}{D/2}=2\frac{L}{D}.
\]

### Topology and contact structure

- full Gauss-linking matrix and integer-lock error;
- component writhe proxy;
- mirror, orientation reversal and rigid-motion checks;
- refined inter-component minimum distance;
- nonlocal self-distance proxy;
- contact graph, degree statistics and cycle rank.

### Vortex dynamics

For every one of the \(2^m\) circulation assignments of an \(m\)-component link:

- regularized native Biot–Savart velocity;
- best rigid translation and rotation;
- normal relative-equilibrium residual;
- geometric impulse;
- Neumann energy proxy;
- soft-core convergence.

The relative-equilibrium score removes tangential reparametrization and tests the normal mismatch against

\[
\mathbf u_{\rm rigid}(\mathbf r)=
\mathbf U+\boldsymbol\Omega\times(\mathbf r-\mathbf r_0).
\]

### Thickness admissibility (G9)

Each link records whether the declared Gilbert diameter \(D\) is attainable:

- `thickness_gate_passes`
- `allowed_diameter_D`
- `binding_constraint` (`curvature` / `self_contact` / `mutual_contact`)
- `curvature_spectral_tail` (\(n^4\)-weighted high-mode power)
- `largest_converged_cutoff` (largest Fourier truncation still within \(\kappa D\le 2\))

### Comparative outputs

- `summary.csv` (includes the five G9 columns above);
- `components.csv`;
- `circulation_sign_configurations.csv`;
- `mutual_contacts.csv`;
- `convergence.csv`;
- `per_link/*.json` (full `thickness_gate` and `curvature_mode_convergence` ledgers);
- correlation, ranking and PCA plots;
- backend, compiler, OpenMP and source-hash provenance.

## Resume safety

A result is resumed only when its signature matches:

- suite version;
- input SHA-256;
- complete preset;
- selected backend;
- native C++ source hash.

Changing the C++ kernel or preset automatically marks existing per-link results stale.

## Scientific status

The source reconstruction, integer linking and C++/Python parity checks are hard validation gates. Mirror ICP, writhe, contact-cycle rank, regularized energy and relative-equilibrium scores are Research-Track diagnostics until the circulation assignment, finite-core profile and governing closure are independently fixed.
