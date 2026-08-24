# SST Finite-Core Axial–Toroidal Eigenmode + Self-Generated Phase-Delay Blind Falsifier v0.1.0

A turnkey Windows/Python/C++ package to test the hypothesis:

\[
\boxed{\text{finite vortex core}+\text{axial/toroidal hybrid mode}+\text{closed propagation}\rightarrow\text{phase-dependent stability window}}
\]

with the critical constraint

\[
\boxed{\text{the delay is measured from the simulation/eigen-dispersion, never supplied as a free restoring parameter.}}
\]

## What is genuinely finite-core here?

The core has radial profiles \(V_\theta(r)\) and \(U_s(r)\). The package solves the linearized incompressible Euler eigenproblem across the core radius and tracks mixed axial/toroidal eigenmodes. It does **not** replace the core by a single Biot–Savart centerline during the eigenmode calculation.

The knot/link centerline supplies closed-loop geometry: length, curvature validity, and Bishop parallel-transport holonomy. The first release is therefore a slender-core local-to-global closure test, not full 3-D finite-core DNS.

## Main null

For each case the active scientific condition satisfies

\[
kL+m\Theta_B=2\pi n.
\]

The matched control uses the same physical parameters but a blinded non-integer phase closure. The scorer does not know which is which.

## Self-generated delay measurement

The finite-core eigenbranch supplies \(\omega(k)\). The code obtains

\[
v_g=d\omega/dk,
\qquad
\tau_g=L/|v_g|,
\]

then actually propagates a narrow packet around the periodic loop and measures \(\tau_{ret}\). The loop phase is recorded; no target phase is used.

## One-click start

```cmd
run_all.cmd
```

This performs environment installation, native C++ build, tests, basic blind preparation/run/seal/reveal.

For the broader campaigns:

```cmd
run_all_extended.cmd
run_all_profile_robustness.cmd
run_all_core_radius.cmd
run_all_chirality_sign.cmd
run_all_radial_convergence.cmd
```

Or:

```cmd
run_all_full.cmd
```

`OMP_NUM_THREADS` defaults to 16 in `_common.cmd`; OpenBLAS and MKL are deliberately pinned to 1 thread because these small generalized eigenproblems are faster and more reproducible without nested BLAS threading.

## Interpretation

`SUPPORTS_SELF_GENERATED_PHASE_FEEDBACK_MECHANISM` is only emitted when all preregistered gates pass: finite-core hybrid-mode validity, independently measured propagation delay, carrier-cluster closed-loop spectral advantage, and out-of-carrier phase→growth predictivity.

A positive v0.1.0 result would justify a full curved finite-core Euler/Floquet calculation. It is not by itself proof of an SST particle or of nonlinear self-confinement.
