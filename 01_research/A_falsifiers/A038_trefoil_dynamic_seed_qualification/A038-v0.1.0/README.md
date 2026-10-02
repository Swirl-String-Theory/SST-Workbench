# SST Trefoil Dynamic Seed Qualification Mega Falsifier v0.1.0

A staged blind Python/C++17/pybind11 campaign for the **current SST question**:

\[
\boxed{\text{Which trefoil start shape most nearly begins as a coherent moving vortex object?}}
\]

The package does **not** assume that the tightest KnotPlot/Ridgerunner geometry is dynamically best. Shape selection itself is a falsifiable, blinded stage.

## Non-negotiable hierarchy

```text
input trefoil sources
    |
    v
S10 blind shape-space generation + discretized contact/isotopy guard
    |
    v
S20 early rolling-onset screen
    |  coherent SE(3) motion vs intrinsic normal deformation
    |  shape-drift AUC, high-k, POD dimension, contact, mesh
    v
S25 blind local refinement around top anonymous seeds
    |
    v
S30 N=64/96/128 resolution qualification
    |
    v
S35 core-radius robustness (.06/.08/.10 default)
    |
    v
S40 long free dynamics + recurrence search
    |
    v
S50 near-RPO + projected Floquet monodromy
    |
    v
S60 finite-core material-vs-fixed causal clock gate
    |  delay DISCOVERED from stretch -> later modal acceleration
    |  target phase NEVER supplied
    v
S70 reveal source identity + deformation parameters
```

The S10 guard assumes candidates are small deformations of an input trefoil and checks discretized nonlocal separation; it is not a standalone knot-polynomial proof.

A downstream gate can never rescue a candidate rejected upstream. Source filename and deformation parameters are hidden until reveal.

## What "rolling" means

The initial physical velocity is decomposed after removing tangential gauge motion. A least-squares rigid motion

\[
\mathbf u_{\perp}(s) \approx \mathbf V + \boldsymbol\Omega\times(\mathbf X-\mathbf X_c)
\]

is fitted in the normal plane. `rolling_coherence` is one minus the normal residual fraction. A good seed therefore has **substantial coherent rigid motion with little intrinsic deformation**, rather than simply having low total velocity.

The early score also includes SE(3)-reduced shape drift, high-wavenumber excitation, POD concentration, contact survival and mesh quality. The exact weights are frozen in each config before the run.

## Stage interpretations

### S20 — seed quality, not orbital stability
A high score means the trefoil **starts well**. It does not imply long-time stability.

### S25 — adaptive discovery, frozen downstream confirmation
The top anonymous early seeds receive a preregistered smaller local deformation cloud. This is explicitly a discovery/optimization step. S30 and later stages provide independent numerical qualification of the resulting candidates.

### S30 — resolution qualification
The same candidate is rerun at N=64/96/128. A winner that moves strongly with N is rejected.

### S35 — core-radius robustness
A seed must remain competitive across the frozen regularized-core ladder before long-run nomination. This prevents one convenient `core_fraction` from defining the winner.

### S40 — long run / recurrence
Long runs use geometry-only tangential mesh redistribution and a global-volume uniform core. The mesh velocity is recorded. Near returns are measured only after rigid/cyclic symmetry reduction.

### S50 — projected Floquet candidate
The package computes a finite-dimensional monodromy matrix on a preregistered Fourier-normal perturbation basis. This is a **projected Floquet diagnostic**, not a claim of full 3N or volumetric 3-D Euler Floquet stability.

### S60 — mechanism only after existence
Only projected-RPO candidates enter the material-core versus fixed-core test. The lag is discovered on the first half of the trajectory and tested on holdout data. The phase is then a measured output

\[
\phi = \omega_{\rm measured}\tau_{\rm measured}\pmod{2\pi},
\]

never a supplied restoring parameter.

## One-click runs

Default dataset:

```text
..\..\KnotPlot\knots\final
```

BASIC:

```bat
run_all.cmd
```

EXTENDED:

```bat
run_all_extended.cmd
```

Production atlas (up to 1024 generated candidates):

```bat
run_all_production.cmd
```

Explicit dataset path is accepted as the first argument.

## Individual stages

```bat
run_00_setup.cmd
run_01_build_native.cmd
run_02_selftest.cmd
run_10_prepare.cmd <dataset> <out> <config>
run_20_early.cmd <out> <config>
run_25_refine.cmd <out> <config>
run_30_resolution.cmd <out> <config>
run_35_core.cmd <out> <config>
run_40_long.cmd <out> <config>
run_50_rpo.cmd <out> <config>
run_60_mechanism.cmd <out> <config>
run_70_reveal.cmd <out>
```

## Current epistemic target

A negative result means progressively more depending on the stage:

- S20 fail: the searched local trefoil shape family contains no strong rolling seed.
- S30 fail: apparent seed quality is resolution-sensitive.
- S40 fail: early rolling does not develop into a recurrent orbit.
- S50 fail: no projected stable near-RPO was certified.
- S60 fail: even if a recurrent projected orbit exists, the tested material-core stretch/delay mechanism does not explain it.

None of these alone is a theorem about every possible finite-core Euler trefoil. The package is deliberately a hierarchy of increasingly strong model-specific falsifiers.
