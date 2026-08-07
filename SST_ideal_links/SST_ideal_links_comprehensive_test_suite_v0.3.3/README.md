# SST Ideal Links Comprehensive Test Suite v0.3.3

v0.3.3 is the **continuum-bridge release** between the v0.3.x QM-readiness machinery and the
v0.4 closure-robustness programme.  It preserves the full geometry/contact/Ridgerunner pipeline and
the C++17/pybind11 Biot–Savart backend, but fixes the two numerical issues exposed by the v0.3.2
`qm_full` campaign:

1. self-interaction exclusion no longer shrinks in physical size when the sampling grid is refined;
2. energy terms are no longer normalized by reference numbers taken from a different sampling grid.

The release remains **Research Track**.  It does not claim that the current closure is the SST
Hamiltonian, nor that a topological link is already a quantum state.

## Main v0.3.3 changes

### 1. Fixed physical self-exclusion arcs

The old Neumann/Biot–Savart self-exclusion was specified as a fixed number of neighbouring segments.
For a component of length \(L_i\) with \(N\) samples, that implied an excluded physical arc of order
\(L_i/N\), so refinement changed the regularization itself.

v0.3.3 adds native and NumPy-parity kernels that exclude by **polygonal arc length**:

\[
\Delta s_{\rm cyc}\le s_{\rm excl},
\qquad
s_{\rm excl}/D=\text{fixed}.
\]

Default full-preset diagnostics use

\[
(s_{\rm excl}^{E}/D,\;s_{\rm excl}^{u}/D)=(0.20,\;0.25).
\]

These values are explicit regularization choices, not CANON constants.

### 2. D-dimensionalized energy ledger

The v0.3.2 sample-derived reference scales are removed from the default QM presets.  Terms are now
reported in the natural diameter units

\[
L/D,
\qquad
D\int\kappa^2ds,
\qquad
E_{\rm rep},
\qquad
E_N/D.
\]

The equal-weight hybrid profile is still only a diagnostic closure.  v0.4 is intended to scan its
weights rather than canonize them.

### 3. Explicit N-continuum audit

A new campaign evaluates the same source geometry at several sampling resolutions while keeping
\(\epsilon/D\) and the physical self-exclusion arcs fixed.

```powershell
.\run_continuum.ps1 -Preset full
```

or directly:

```powershell
python scripts\run_continuum.py `
  --config configs\qm_full.json `
  --ids L2a1 L4a1 L6a4 L6n1 L7n2 `
  --require-native --skip-native-build
```

The full preset uses

\[
N=96,192,384
\]

and reports last-pair relative changes plus a Richardson estimate when the data permit one.

### 4. Symplectic-kernel audit and algebraic quotient candidate

If the candidate filament two-form is singular, v0.3.3 now records its SVD nullspace and the reduced
basis coordinates dominating each null vector.  It also constructs the algebraic image-space form

\[
\Omega_Q=Q^T\Omega Q.
\]

A corresponding projected Hamiltonian spectrum can be calculated.  This is **not** automatically a
physical gauge quotient: the null directions may be gauge, Casimir directions, or evidence of an
incomplete reduced model.

This is especially relevant to the Hopf baseline, where v0.3.2 found a two-dimensional kernel.

### 5. Local stationary-background probe

For full/max runs, the best sector receives a trust-limited Newton probe

\[
\delta q_N=-H^+\nabla E,
\]

followed by nonlinear line-search evaluations of the actual finite-difference gradient.  The output
asks whether the source Fourier geometry has a nearby lower-gradient configuration in the current
reduced closure.  It is not a substitute for a full topology-preserving finite-core optimizer.

### 6. Borromean bookkeeping

`L6a4` is catalogued as the **Borromean rings**.  The ledger records the catalog fact
\(|\bar\mu_{123}|=1\), but v0.3.3 does **not** claim to numerically derive the Milnor invariant from
the sampled curves.  `higher_linking_invariant_computed` therefore remains false.

## Recommended workflow before v0.4

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
python run_native_preflight.py --force
python run_native_audit.py --build-verbose
.\run_continuum.ps1 -Preset full
python scripts\run_qm.py --preset full --ids L2a1 L4a1 L6a4 L6n1 L7n2 --require-native --skip-native-build
```

After activation, use `python`, not `py -3`, so build/import/run use the same Python ABI.

## Current Q1–Q5 interpretation

- **Q1:** integer pair-linking sector ledger; higher invariants remain explicit dependencies when
  pairwise linking vanishes.
- **Q2:** candidate classical background from rigid-motion residual plus reduced closure gradient.
- **Q3:** full reduced Hessian only after step-size and spatial convergence checks are inspected.
- **Q4:** candidate filament two-form; singular kernels are now explicitly diagnosed.
- **Q5:** dimensionless linearized Hamiltonian spectrum.  No \(\hbar\omega\) particle spectrum is
  inferred.

The `quick` preset remains a screening run.  `full` uses off-diagonal central-difference Hessians.
`max` is intended only for candidates that survive the continuum audit.

## Requested low-crossing set

```text
L2a1 L4a1 L5a1
L6a1 L6a2 L6a3 L6a4 L6a5 L6n1
L7a1 L7a2 L7a3 L7a4 L7a5 L7a6 L7a7 L7n1 L7n2
```

The included Gilbert source contains 130 links through nine crossings.

## Main outputs

QM campaign:

- `qm_readiness_summary.csv`
- `topological_quantum_labels.csv`
- `sector_readiness.csv`
- `normal_modes.csv`
- `candidate_symplectic_forms.csv`
- `per_link/*.json`
- `QM_REPORT.md`

Continuum campaign:

- `continuum_summary.csv`
- `per_link/*.json`
- `continuum_metadata.json`

## Native policy

No precompiled `.pyd` or `.so` is distributed.  Build locally for the active Python ABI.  The native
parity audit now covers both the legacy segment-count kernels and the new fixed-arc-exclusion kernels.
