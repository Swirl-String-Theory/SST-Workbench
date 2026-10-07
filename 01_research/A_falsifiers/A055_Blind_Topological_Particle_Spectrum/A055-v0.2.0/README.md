# A055 Blind Topological Particle Spectrum Falsifier v0.2.0

## Scientific purpose

v0.2.0 replaces the v0.1.x PD-derived energy proxies with the existing SST-Workbench production evidence chain wherever that chain is scientifically available:

```text
A055 topology census (82 objects)
        ↓
E010 PKLSA v0.3.1 geometry/source qualification
        ↓
E011 SKLSA v0.3.0 STATIC_READY independent provider anchors
        ↓
C006 v0.3.0 regularized Biot–Savart projected Kelvin generator
        ↓
E012-v0.2.0-style eigenvalue + eigenvector branch tracking
        ↓
same-generator RPO conditioning
        ↓
cross-provider dynamic agreement
        ↓
conditional true relative-return Floquet monodromy
        ↓
sealed BLIND dynamic spectrum
        ↓
historical 5_2 / 6_1 + SM/Higgs mass-pattern reveal
```

The historical VAM/SST quark hypothesis remains reveal-only:

\[
u\leftrightarrow5_2,\qquad d\leftrightarrow6_1.
\]

## Critical link-sector boundary

C006/E012 currently owns a **one-centerline counter-channel** dynamical contract. A055 v0.2.0 therefore does **not** reinterpret that solver as a multi-component link solver. Links retain their topology and PKLSA STATIC_READY evidence, but receive:

`LINK_DYNAMICS_NOT_IMPLEMENTED_V0_2`

and are excluded from dynamic particle-mass fitting.

This is deliberate fail-closed behavior. A future link-dynamics release must preregister the multi-component circulation/sign, core, gauge, RPO and monodromy contracts before links can be dynamically ranked against knots.

## Provider normalization

For each independent E011 knot provider:

\[
D_{\rm eff,raw}=\frac{L_{\rm raw}}{\mathcal R_{\rm E011}},\qquad
\mathbf X'=\frac{\mathbf X}{D_{\rm eff,raw}}.
\]

Thus \(D_{\rm eff}=1\) and source coordinate conventions cannot masquerade as physical scale differences.

## Dynamic branch qualification

For every preregistered Kelvin mode \(m\), the finest-resolution C006 positive-frequency root is tracked backward through the resolution ladder using

\[
C_{ij}=\frac12 d_\lambda+\frac12(1-O_v),
\]

with normalized eigenvalue distance \(d_\lambda\) and complex eigenvector overlap \(O_v\).

The selected branch must pass:
- resolution shift tolerance;
- adjacent eigenvector overlap;
- oscillatory quality \(|\Re\lambda|/|\Im\lambda|\);
- same-generator RPO conditioning;
- cross-provider agreement.

## True Floquet gate

Only after the dimensionless dynamic gate passes does v0.2.0 call C006's **true relative-return monodromy**. This differentiates the nonlinear time-\(T\) flow map of the accepted RPO with its fixed return group action.

The restricted Kelvin block must satisfy frozen bounds on:
- base relative-map residual;
- neutral time-tangent residual;
- Kelvin-subspace leakage;
- Floquet multiplier modulus deviation.

No true-Floquet claim is made if the RPO gate is closed.

## Run

Production quick campaign:

```bat
run_all.cmd quick C:\workspace\projects\SST-Workbench
```

Full campaign:

```bat
run_all.cmd full C:\workspace\projects\SST-Workbench
```

Preserve blindness:

```bat
run_blind_only.cmd full C:\workspace\projects\SST-Workbench
```

Portable package validation, with no Workbench physics:

```bat
run_ci.cmd
```

`ci` proves package integrity only; it cannot promote any topology.

## Outputs

- `BLIND/FEATURES.json`
- `BLIND/dynamics/CASE_*.json`
- `BLIND/GATES.json`
- `BLIND/BLIND_SEAL.json`
- `REVEALED/HISTORICAL_5_2_6_1_DYNAMIC_CHECK.json`
- `REVEALED/SM_DYNAMIC_MASS_PATTERN_SEARCH.json`
- `REVEALED/GLOBAL_LOOK_ELSEWHERE.json`
- separate BLIND / REVEALED / combined ZIPs

## Interpretation boundary

A mass-ratio resemblance is never sufficient for particle identity. v0.2.0 does not infer electric charge, color, weak isospin, spin, lifetime or coupling constants from topology. A W/Z/H ratio match is explicitly **not** a scalar-Higgs identification.
