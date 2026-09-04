# SST Ideal Links Comprehensive Test Suite v0.3.1

This release keeps the complete v0.2.1 geometry, topology, contact-map, C++17/pybind11
Biot–Savart and Ridgerunner-export pipeline, and adds a separate **QM-readiness campaign**.

The QM campaign does not assume that a topological link is already a quantum state. It asks whether
a selected classical link background has enough mathematical structure to justify a later
quantization attempt:

\[
\text{discrete sectors}
\rightarrow
\text{classical background}
\rightarrow
\text{reduced Hessian}
\rightarrow
\text{candidate two-form}
\rightarrow
\text{linear spectrum}.
\]


## v0.3.1 Windows native preflight

A clean extraction has no universal `.pyd`; it must build one for the active Python ABI.

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
python run_native_preflight.py --force
.\run_qm.ps1 -Preset quick
```

After a successful preflight:

```powershell
python scripts\run_qm.py --preset quick --require-native --skip-native-build
```

Use `python`, not `py -3`, after activating the virtual environment.


## Requested low-crossing set

The default geometry campaign remains the first 18 ideal links through seven crossings:

```text
L2a1 L4a1 L5a1
L6a1 L6a2 L6a3 L6a4 L6a5 L6n1
L7a1 L7a2 L7a3 L7a4 L7a5 L7a6 L7a7 L7n1 L7n2
```

The included Gilbert source also supports the complete 2–9 crossing database.

## What v0.3.0 adds

### Q1 — topological and circulation sectors

- integer-locked Gauss-linking form;
- component permutation/automorphism proxy;
- quotient of all \(2^m\) circulation assignments by component permutations and global reversal;
- linking-form rank, nullity, determinant and pair-linking gcd;
- explicit flag when a three-component link has zero pairwise linking and therefore requires a
  higher invariant such as a Milnor or multivariable Alexander calculation.

The package does not fabricate unresolved higher invariants.

### Q2 — reduced classical background

The fixed-core v0.2.1 relative-equilibrium residual at

\[
\epsilon/D=0.10
\]

is combined with a reduced energy-gradient test. This selects candidate backgrounds without claiming
that the source Fourier geometry is an exact finite-core stationary solution.

### Q3 — normal perturbations and Hessians

For each component, a periodic rotation-minimizing frame is constructed. Low Fourier harmonics in the
two normal directions generate perturbations. Translation and rotation gauge directions are removed.

Central finite differences produce termwise gradients and Hessians for:

- total centerline length;
- bending integral;
- a smooth sampled tube-overlap penalty;
- regularized Neumann energy.

Geometric derivatives are computed once and reused across all independent circulation sectors.

### Q4 — candidate symplectic structure

The Research-Track filament two-form is

\[
\Omega_{ab}
=
\sum_i \sigma_i
\oint
\hat{\mathbf t}_i\cdot
\left(
\delta\mathbf X_a\times\delta\mathbf X_b
\right)
\,ds.
\]

The campaign records antisymmetry, rank, nullity, singular values and a determinant/Pfaffian proxy.
Full rank after gauge reduction is treated only as a necessary readiness condition.

### Q5 — linearized Hamiltonian spectrum

For each declared effective energy profile,

\[
\Omega\dot{\mathbf q}=H\mathbf q,
\qquad
A=\Omega^{+}H.
\]

The suite reports:

- unstable real eigenvalue content;
- oscillatory mode count;
- Hamiltonian \(\lambda\leftrightarrow-\lambda\) pairing error;
- positive dimensionless frequencies;
- frequency ratios to the lowest mode.

It deliberately does **not** convert these into \(\hbar\omega\) energies. An absolute action scale,
canonical normalization and accepted SST symplectic derivation are still missing.

## Explicit energy profiles

The presets include three transparent Research-Track closures:

```json
"geometric_tube": {
  "length": 1.0,
  "bending": 1.0,
  "tube_repulsion": 1.0,
  "neumann": 0.0
}
```

```json
"hydrodynamic_proxy": {
  "length": 0.0,
  "bending": 0.0,
  "tube_repulsion": 0.0,
  "neumann": 1.0
}
```

```json
"hybrid_equal_normalized": {
  "length": 0.25,
  "bending": 0.25,
  "tube_repulsion": 0.25,
  "neumann": 0.25
}
```

Each term is normalized by its baseline magnitude. These weights are assumptions in configuration,
not CANON definitions.

## Install and validate

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
python -m sst_link_suite.cli build-native --force --strict --verbose
python -m pytest
python run_native_audit.py --force-build --build-verbose
```

After activation, use `python`, not `py -3`, so compilation, import and execution use the same ABI.

## Recommended first QM campaign

The shortest scientifically useful shortlist is:

\[
L2a1,
L4a1,
L5a1,
L6a4,
L6n1,
L7n1.
\]

The `quick` preset uses a **diagonal Hessian screen**. It can rank Q1–Q2 candidates rapidly,
but it is intentionally barred from passing Q3–Q5. Use `full` or `max` for the complete off-diagonal
Hessian and linear Hamiltonian audit.

Run the screen with:

```powershell
.\run_qm.ps1 -Preset quick
```

Equivalent direct command:

```powershell
python scripts\run_qm.py `
  --preset quick `
  --ids L2a1 L4a1 L5a1 L6a4 L6n1 L7n1 `
  --require-native `
  --native-threads 16
```

Higher-resolution campaign:

```powershell
.\run_qm.ps1 -Preset full
```

All 18 low-crossing links:

```powershell
python scripts\run_qm.py --preset quick --require-native --ids `
  L2a1 L4a1 L5a1 L6a1 L6a2 L6a3 L6a4 L6a5 L6n1 `
  L7a1 L7a2 L7a3 L7a4 L7a5 L7a6 L7a7 L7n1 L7n2
```

The all-database option exists, but a 130-link Hessian campaign should only be started after the
shortlist has established sensible profiles and convergence behavior:

```powershell
python scripts\run_qm.py --preset quick --all-database --require-native
```

## QM outputs

- `qm_readiness_summary.csv`: best independent circulation sector per link;
- `topological_quantum_labels.csv`: linking form, automorphism proxy and higher-linking flag;
- `sector_readiness.csv`: complete independent-sector gate ledger;
- `normal_modes.csv`: dimensionless mode frequencies and ratios;
- `candidate_symplectic_forms.csv`: rank, nullity and singular spectrum;
- `normal_bundle_holonomy.csv`: rotation-minimizing-frame closure angles;
- `per_link/*.json`: complete gradients, Hessians, matrices and spectra;
- `QM_REPORT.md`: compact comparative report;
- `qm_run_metadata.json`: input hash, backend, config, timing and failures.

## Existing geometry and Ridgerunner campaigns

The v0.2.1 commands remain available:

```powershell
.\run_all_chunked.ps1 -Preset full
```

```powershell
python -m sst_link_suite.cli export-ridgerunner `
  --input data\idealLinks.txt `
  --output ridgerunner_inputs `
  --sample-n 2048
```

Ridgerunner remains an independent second-stage geometry/contact audit. It does not replace the
Gilbert Fourier baseline and is not itself the QM mechanism.

## Scientific status

- Integer Gauss-linking and native/Python parity are hard numerical checks.
- Normal-frame holonomy is geometric, not a Berry phase.
- The reduced energy profiles, candidate filament two-form and linear spectra are **Research Track**.
- A level-5 readiness result means that a quantization method can be attempted on the reduced model.
- It does not derive Hilbert space, Born probabilities, operator commutators, \(\hbar\), or measured
  particle spectra.

See `docs/QM_READINESS_GATES.md` for the exact gate semantics.
