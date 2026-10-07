# A055 Blind Topological Particle Spectrum Falsifier v0.2.1

A055 v0.2.1 is a focused production-repair release over v0.2.0.

## Production chain

```text
82-object frozen topology atlas
        ↓
E010 PKLSA v0.3.1 / E011 SKLSA v0.3.0 source-qualified geometry
        ↓
provider parser: Gilbert AB / VECT / XYZ
        ↓
STRICT C006-v0.3.0 native build + parity preflight
        ↓
C006 projected Kelvin generator + overlap-aware branch tracking
        ↓
same-generator RPO
        ↓
cross-provider agreement (minimum two preregistered providers)
        ↓
conditional true relative-return monodromy/Floquet
        ↓
sealed BLIND spectrum
        ↓
historical 5_2/6_1 and SM/Higgs mass-pattern reveal
```

## Repair 1 — XYZ is supported

PKLSA/KnotPlot sources with

```json
"representation": "xyz"
```

are now parsed as closed one-component curves, arclength-resampled, orientation-normalized and scaled using the E011-certified ropelength.

## Repair 2 — missing second provider is not a false dynamics failure

When E011 is STATIC_READY but only one requested provider is present:

```text
SINGLE_PROVIDER_ONLY
```

The available provider is still allowed to produce Kelvin/RPO diagnostics. However:

\[
N_{\rm provider}<2
\quad\Longrightarrow\quad
\text{particle promotion}=FAIL.
\]

This preserves useful numerical evidence without pretending that cross-provider validation occurred.

## Repair 3 — C006 native backend is mandatory

Every production run performs:

1. C006 build/import;
2. require backend name `cpp`;
3. deterministic native/Python `pair_rhs` parity check.

Frozen defaults:

\[
\frac{\|f_{\rm cpp}-f_{\rm py}\|_2}{\|f_{\rm py}\|_2}\le10^{-10},
\qquad
\|f_{\rm cpp}-f_{\rm py}\|_\infty\le10^{-11}.
\]

If this gate fails, the BLIND campaign does not start. Silent Python fallback is prohibited in production.

## Campaign identity

```bat
run_all.cmd quick
```

writes:

```text
A055_Blind_Topological_Particle_Spectrum_Falsifier_v0.2.1-quick-outputs
```

while:

```bat
run_all.cmd full
```

writes:

```text
A055_Blind_Topological_Particle_Spectrum_Falsifier_v0.2.1-full-outputs
```

The frozen config also records `A055-v0.2.1-quick` or `A055-v0.2.1-full`.

## Recommended run

```bat
run_all.cmd full
```

Your canonical Workbench path remains the built-in default:

```text
C:\workspace\projects\SST-Workbench
```

An explicit second argument is only needed on another machine/root.

To preserve blindness:

```bat
run_blind_only.cmd full
```

## Link boundary

Multi-component links remain static/topological-only in v0.2.1. C006's one-centerline counter-channel model is not silently reinterpreted as a physical multi-component link solver.

## Interpretation boundary

A055 v0.2.1 still cannot establish particle identity from a mass ratio alone. Electric charge, color, weak quantum numbers, spin, lifetime and couplings require independent gates.
