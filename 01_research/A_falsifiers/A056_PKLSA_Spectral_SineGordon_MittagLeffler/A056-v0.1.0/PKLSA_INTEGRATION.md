# PKLSA integration boundary — A056 v0.1.0

A056 is designed for the repository-native E010 PKLSA route, but **E010 geometry alone is not enough** to evaluate the Sine–Gordon or Mittag-Leffler hypotheses. Both hypotheses require a time-dependent phase/ringdown observable.

## Upstream authority

The current Workbench pattern treats E010 PKLSA v0.3.1 `RELEASE.json`, per-topology qualification material, carrier envelopes, source-independence metadata and original source bytes as geometry authority. Downstream consumers are expected to re-check raw and decoded-geometry hashes rather than copying geometry into a new untracked source family.

Default Workbench root:

```text
C:\workspace\projects\SST-Workbench
```

## Required A056 chain

\[
\text{qualified E010 carrier}
\rightarrow
\text{finite-core/Euler perturbation provider}
\rightarrow
\varphi(t,s),\;R(t)
\rightarrow
\text{A056 blind competition}.
\]

The dynamic provider must freeze an operational definition of the phase field \(\varphi(t,s)\) before A056 scoring. Examples could be material-frame torsion phase, a Kelvin-mode phase coordinate, or another explicitly defined angular observable. A056 deliberately does not invent that mapping from geometry after seeing results.

`tools/convert_pklsa_npz.py` is therefore an **adapter for dynamical provider output**, not a substitute for E010's geometry loader.

## Independence

E010 `independence_group` is useful provenance/stratification metadata but does not automatically create independent dynamical replications. A056 `source_group` must represent an independently generated physical-provider lane according to the preregistration. Mesh/timestep refinements of the same carrier remain numerical replications, not independent evidence.

## Fail-closed requirement

If only static XYZ/VECT/Fourier geometry is available, A056 must stop before G3/G4. Static geometry can qualify the upstream carrier but cannot establish a dynamic phase potential or memory kernel.
