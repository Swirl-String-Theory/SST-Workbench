# E012 PKLSA Dynamic Eigenmode Extractor v0.2.0

Trefoil-first dynamic-qualification pipeline between the E011 SKLSA seed atlas,
C006 Kelvin/Floquet dynamics, A052 dispersion closure, and ultimately A044.

v0.2.0 addresses the three limitations exposed by the real v0.1.x full run:

1. the background is explicitly subjected to a **same-generator relative-periodic-orbit (RPO) qualification**;
2. mode identity is tracked across resolution with **complex eigenvector/subspace overlap** in addition to eigenvalue distance;
3. the result must reproduce across **multiple independent E011 provider anchors** (`gilbert` and `knotplot`) before a consensus branch can be handed downstream.

## Scientific chain

```text
E010 geometry/source/topology qualification
        ↓
E011 STATIC_READY provider anchors
   ┌────┴────┐
 Gilbert   KnotPlot
   │          │
   ├─ same-generator RPO qualification
   ├─ C006 projected temporal Kelvin generator
   ├─ eigenvalue + eigenvector branch tracking across N
   └─ qualified mode subset
        ↓
Cross-provider dynamic agreement
        ↓
E012 dimensionless consensus branch
        ↓  only with independent SI/energy contract
A052
        ↓
A044
```

## Important methodological changes

### Provider normalization

The source archives use different coordinate conventions. E012 therefore does not
compare raw coordinate scales. For every E011 provider anchor it uses the E011
certified ropelength to define

\[
D_{\rm eff,raw}=\frac{L_{\rm raw}}{\mathcal R_{\rm E011}},
\]

then rescales the centerline so that \(D_{\rm eff}=1\). Hence

\[
\hat k_m=\frac{2\pi m}{\mathcal R_{\rm E011}}.
\]

This rule is frozen before the first v0.2.0 scientific run and contains no A044 or
GRB target value. Provider orientation is canonicalized to positive signed writhe
before dynamics so opposite source-file orientation cannot masquerade as a provider
disagreement.

### Eigenvector branch identity

At the finest spatial resolution C006 supplies the selected positive-frequency root.
E012 anchors branch identity there and tracks backward over the N-ladder using a
Hungarian assignment with the frozen cost

\[
C_{ij}=\tfrac12 d(\lambda_i,\lambda_j)
      +\tfrac12\left(1-|v_i^\dagger v_j|\right).
\]

A selected branch must satisfy both the inherited resolution shift tolerance and
adjacent eigenvector overlap \(\ge 0.80\). It must also remain genuinely oscillatory,
with \(|\Re\lambda|/|\Im\lambda|\le1\), at every level.

The old C006 full-spectrum Hungarian tracking is still emitted as a diagnostic. It is
no longer used as a surrogate for identity of one specific propagation branch.

### RPO conditioning

For each provider E012 runs C006 `search_relative_periodic_orbit` with exactly the
same offset, regularization, channel phase and circulation signs as the spectral
generator. No parameter scan is allowed. The C006 recurrence acceptance rule is
used unchanged. v0.2.0 requires this RPO gate for a dimensionless downstream handoff.

An accepted RPO is **not** called true Floquet evidence. Monodromy is not computed in
v0.2.0. The background rigid-frame residual remains a diagnostic rather than being
forced through a newly invented post-hoc threshold.

## Frozen presets

`quick`: `N=24,32,40`, `m=1..3`, spectral shift tolerance `0.20`, RPO at `N=32`.

`full`: `N=40,56,72,88`, `m=1..5`, spectral shift tolerance `0.12`, RPO at `N=56`.

Cross-provider consensus requires at least three common qualified modes. For each
mode the independent provider span must be <= 0.20 in both `omega_hat` and `kD`.
These are method thresholds, not physical constants and not target-fitted values.

## Run

```bat
run_all.cmd C:\workspace\projects\SST-Workbench --preset full
```

The runner prefers Python 3.13 so the existing C006 `cp313` native module can be
loaded. `--force-python` remains available for reference/parity work.

## Principal outputs

```text
outputs/
  E012_RUN_CONTEXT.json
  E011_PROVIDER_SEEDS.json
  C006_PROVENANCE.json
  RPO_CONDITIONING.json
  DYNAMIC_EIGENMODE_LEVELS.json
  PROVIDER_DYNAMIC_BRANCHES.json
  CROSS_PROVIDER_AGREEMENT.json
  DYNAMIC_EIGENBRANCH.json
  GATES.json
  A052_HANDOFF_STATUS.json
  a052_dynamic_candidate.json   # only after all dynamic + independent SI gates pass
  report.md
```

## Interpretation boundary

A v0.2.0 pass would establish only a numerically reproducible, cross-provider,
RPO-qualified dimensionless Kelvin branch under the declared C006 regularized
Biot-Savart closure. It does not by itself identify a photon, prove true Floquet
stability, determine a physical length/circulation scale, or fit GRB 221009A.
