# Preregistration Template

Use this file before running a campaign intended to support a prediction claim.

## A. Claim

**Primary observable:**

```text
Example: energy_proxy_ratio for trefoil / ring
```

**Primary hypothesis:**

```text
Example: the ratio converges to one kernel-stable value within 1%.
```

**Null/falsifier:**

```text
Example: the ratio shifts by more than 5% across admissible kernels or resolutions.
```

## B. Frozen model

- Governing operator:
- Core kernel:
- Core radius \(\epsilon\):
- Circulation:
- Density convention:
- Boundary/domain treatment:
- Tangential gauge treatment:
- Reconnection rule:
- Topology policy:

## C. Frozen geometry sources

- Ring source:
- Trefoil source:
- Mirror source:
- Figure-eight source:
- Radius/diameter convention:
- Smoothing/reconstruction rule:

## D. Normalization

Choose exactly one:

- [ ] fixed centerline length;
- [ ] fixed RMS radius;
- [ ] fixed certified reach;
- [ ] fixed tube volume with separately derived core radius;
- [ ] other, fully specified.

## E. Numerical ladder

- Resolutions:
- Time steps:
- Quadrature orders:
- Core radii:
- Kernels:
- Remesh frequencies:
- Domain sizes:

## F. Acceptance thresholds

- Relative-equilibrium residual:
- Energy drift:
- Length drift:
- Recurrence error:
- Ratio convergence:
- Kernel spread:
- Topology certificate:

## G. Dependency exclusion

Confirm that none of the following sets an input:

- [ ] \(\alpha\);
- [ ] \(m_e\);
- [ ] \(G\);
- [ ] \(L_p\);
- [ ] \(a_0\);
- [ ] Rydberg constant;
- [ ] target experimental ratio;
- [ ] an equivalent algebraic representation of the target.

## H. External comparison

- Benchmark code or experiment:
- Observable definition:
- Matching boundary conditions:
- Blinding procedure:
- Date of parameter freeze:

## I. Reporting rule

All runs are reported, including failed resolutions, kernels and initial conditions. No branch is removed after target comparison unless the exclusion criterion was preregistered.
