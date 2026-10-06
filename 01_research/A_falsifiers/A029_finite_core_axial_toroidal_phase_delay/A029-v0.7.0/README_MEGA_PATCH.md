# A029 v0.6.0 → v0.7.0 — Specific-Lagrangian Mega Falsifier

This is the revised v0.7.0 patch built **on top of the actual sealed v0.6.0 producer**.

The v0.6.0 file

`src/sst_finite_core_falsifier/sst_lagrangian.py`

is hash-guarded at

`df880fdb1814ad568728506033ade1b15fde42c6726fdad854a7ecbc706136a0`

and is **not overwritten**.  The user-supplied v0.6.0 output archive proved that this producer was present in the sealed source tree, but that the normal v0.6.0 campaign did not actually emit a delta-l/action-kernel campaign.  v0.7.0 therefore adds orchestration and certification around the parent producer rather than replacing it.

## One production command

From the A029-v0.6.0 project root:

```cmd
python path\to\this_patch\apply_mega_patch.py
run_specific_lagrangian_mega.cmd
```

The default run requires the native C++/pybind11 backend and executes the complete local test suite first.

A non-certifying Python smoke run is explicitly available:

```cmd
run_specific_lagrangian_mega.cmd --diagnostic-python --limit 2
```

Any `--limit` run is labelled diagnostic even when the native backend is available.

## What changed relative to the earlier v0.7 draft

The most important correction is conceptual:

\[
K_\ell(\Delta)
=L_\ell(0)-\frac{L_\ell(-\Delta)+L_\ell(+\Delta)}{2}
\]

is a **finite symmetric-control residual**.  For a smooth same-branch continuation,

\[
K_\ell(\Delta)=O(\Delta^2).
\]

Therefore a non-zero value at the frozen `Delta=0.37` is not by itself an intrinsic action or topological invariant.

v0.7.0 now treats the local wavenumber curvature

\[
C_k
=-\frac{2K_\ell}{(\delta\hat{k})^2}
\approx
\frac{\partial^2 L_\ell}{\partial\hat{k}^2}
\]

as the primary **certification diagnostic**, with

\[
\delta\hat{k}=\frac{2\pi\Delta}{\hat L}.
\]

It then uses two smallest detunings for Richardson extrapolation to `delta k -> 0` before radial-resolution certification.  This removes the loop-length dependence that would be hidden if one normalized only by `Delta^2`.

A second correction is equally important: the complex A029 eigenvector has an arbitrary global phase.  Therefore a real

\[
\delta\ell_{\rm SST}(t)
\]

cannot be certified from the eigenproblem alone.  v0.7.0 requires an independent predictor-clean raw modal trajectory whose complex `a(t0)` is projected onto the **exact same normalized basis hash**.  It then obtains

\[
a(t_0)=\epsilon e^{i\phi_0},
\]

so amplitude and physical phase origin are fixed together, without fitting an attosecond observable.

Finally, even a certified `C_k` is not itself a physical action.  The action stage remains `NOT_RUN` until an independent physical reference provides `physical_delta_k_hat`.  Only then is

\[
K_{\rm phys}(t)
\simeq
-\frac12 C_k(t)(\delta\hat{k}_{\rm phys})^2
\]

converted into

\[
\delta \ell_{\rm SST}(t),
\qquad
\delta s_{\rm SST}(t)=\int\delta\ell_{\rm SST}\,dt.
\]

## Ordered pipeline

The single run executes all stages in order.  Missing prerequisites do not abort the scientific record; the corresponding downstream gate becomes machine-readable `NOT_RUN`.

| Stage | Purpose | Primary output |
|---|---|---|
| 00 | Verify sealed v0.6 parent, backend, config and create fresh blind catalog | parent/config provenance |
| 01 | Evaluate finite `K_l` and local `C_k` for every blind pair | full radial complex kernels |
| 02 | Test `K ~ delta_k^2`, Richardson `C_k(delta k→0)`, radial convergence and same-branch stability | certified `C_k0(r,t)` |
| 03 | Match independent raw nonlinear/modal trajectory by geometry+basis hash | `epsilon`, `phase0` |
| 04 | Require clean physical scale + independent `physical_delta_k_hat` + A042/QGI action scale | SI `delta l`, `delta s`, `delta phi` |
| 05 | Characterize radial coherence and cancellation of the extrapolated curvature field | radial metrics |
| 06 | Rigid-rotation hard gate; mirror/orientation characterization | transformation metrics |
| 07 | Apply only a physically derived, frozen, source-hash-linked A029→Volkov mapping matrix | attosecond forward prediction |

Blind outputs are sealed before the private carrier/family mapping is read.  Reveal adds grouping only; it never mutates the blind tree.

## Production size

The default fresh blind campaign contains 96 pairs:

`6 carriers × 2 profiles × 4 axial ratios × 1 core fraction × m=1 × 2 n-values`.

Stage 02 is intentionally expensive.  For each parent-qualified case it uses radial levels

`28, 36, 44, 56, 72`

and detuning scales

`1, 1/2, 1/4, 1/8`.

The two smallest detunings at every radial level form the Richardson estimate; the highest radial level additionally performs the full detuning-null fit.

## Fail-closed external contracts

Templates are supplied under `templates/`.  They are intentionally invalid by default.

- `physical_scale_provenance.template.json`
- `reference_contract.template.json`
- `raw_amplitude_contract.template.json`
- `attosecond_mapping_manifest.template.json`

Do not change dependency flags merely to make a gate pass.  They are provenance assertions.

## Outputs

Default output folder:

`A029-v0.7.0-outputs/`

and packages:

- `A029-v0.7.0-outputs.zip`
- `A029-v0.7.0-outputs_BLIND.zip`
- `A029-v0.7.0-outputs_REVEALED.zip`

The private prepare key is kept outside all packaged outputs.

### Adaptive high-resolution extension

The local diagnostic showed that a case can satisfy the `Delta -> 0` law while still failing radial convergence by `N=72`.  The production-native run therefore performs an **adaptive** extension to `N=88,104` only when the detuning-null gate passes but the initial radial-curvature gate fails.  Python-fallback diagnostics skip this expensive extension and report that fact explicitly; they cannot certify the case.
