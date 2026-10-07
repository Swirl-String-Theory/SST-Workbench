# PKLSA / dynamic-provider integration for A056 v0.2.3

The intended physical evidence chain remains

\[
\text{qualified E010/PKLSA carrier}
\rightarrow \text{finite-core/Euler perturbation provider}
\rightarrow \{t,s,\varphi(t,s),R(t)\}
\rightarrow \text{A056}.
\]

A056 does not synthesize time dependence from a static PKLSA centerline. The provider must freeze `phase_definition_id` before A056 scoring. Real physical evidence also requires explicit `independence_unit`, `provenance_family`, `upstream_geometry_sha256` and `carrier_sha256` metadata.

For conservative Euler-like providers, a decaying projected mode envelope is interpreted as dephasing/energy transfer unless an independently modeled dissipative mechanism is present.
