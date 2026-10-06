# A052 Link-Field Photon Dispersion Closure Falsifier v0.1.0

Scientific gate between the PKLSA geometry/topology pipeline and the A044 cosmic-gamma propagation falsifier.

## Question

Can the current PKLSA route supply an **independently derived dynamical photon/eigenmode dispersion law** \(\omega(k)\), from which \(v_g=d\omega/dk\) and \(\delta(E)=1-v_g/c\) can be computed without fitting GRB 221009A?

## Core policy

Geometry alone is not promoted to a wave dispersion law. A qualifying candidate must contain dynamical evidence: a time-dependent field or a linearized evolution operator, an identified propagating eigenmode, resolved \((k,\omega)\) samples, convergence evidence, and no astrophysical target fit.

The current E010 PKLSA v0.3.1 release is used only as a provenance-frozen source snapshot. Its own release boundary states that it is a geometry/source/topology qualification layer, not a dynamical-stability claim.

## Outputs

- `outputs/blind/`: frozen admissibility rules only.
- `outputs/revealed/`: inspection of the current PKLSA snapshot against those rules.
- `outputs/revealed/a044_candidate.json`: emitted only when all hard dynamical gates pass.

## One-click Windows

```bat
run_all.cmd
```

## Interpretation

`BLOCKED_NO_DYNAMICAL_EIGENMODE_DATA` is not a falsification of SST. It is a falsification of the stronger claim that the present PKLSA geometry layer already establishes a photon propagation dispersion law.
