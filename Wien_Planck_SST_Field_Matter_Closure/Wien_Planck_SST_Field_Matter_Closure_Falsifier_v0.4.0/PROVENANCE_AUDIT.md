# Provenance audit — v0.4.0

## Scope

v0.4.0 changes the *discovery population and computational funnel*, not the anti-circularity rule of the Universal-Action test. The release embeds the self-contained **SST Parametric Knot–Link Seed Atlas (PKLSA) v0.1.0** and screens all 2352 candidates before CPU reference qualification.

The provenance roles are deliberately separated:

| Artifact / input | Epistemic role | Used before reveal? | May determine absolute Planck scale? |
|---|---|---:|---:|
| PKLSA v0.1.0 geometry | discovery data | yes | no |
| SYCL Stage-1/2 metrics | coarse discovery/screening data | yes | no |
| CPU C++/pybind11 seed qualification | confirmatory carrier qualification | yes | no |
| frozen-mode action campaign | confirmatory dimensionless dynamics | yes | no |
| legacy SST constants | historical / contaminated control | no | no |
| independent SI normalization | optional post-reveal calibration | reveal only | only if provenance-independent |

## Universal-Action anti-circularity

The legacy relation

\[
4\pi^2\rho_{\rm core}\,v_{\circlearrowleft}r_c^4\simeq h
\]

is not an independent prediction when the upstream SST definitions contain

\[
v_{\circlearrowleft}=\frac{\alpha c}{2},
\qquad
F_{\rm swirl}^{\max}=\frac{v_{\circlearrowleft}\hbar}{2r_c^2},
\]

and

\[
\rho_{\rm core}
=\frac{4F_{\rm swirl}^{\max}}{\pi\alpha^2c^2r_c^2}.
\]

Substitution algebraically forces

\[
4\pi^2\rho_{\rm core}v_{\circlearrowleft}r_c^4
=2\pi\hbar=h.
\]

Likewise, an action scale

\[
J_0=\rho\Gamma L^3
\]

becomes circular if the reveal mapping uses

\[
\rho=\rho_{\rm core},\qquad
\Gamma=2\pi r_cv_{\circlearrowleft},\qquad
L=r_c,
\]

because this implies \(J_0=\hbar\) under the same legacy chain. This mapping remains a **contaminated negative control** and can never establish an independent Planck-scale prediction.

The pre-reveal v0.4.0 Universal-Action path therefore uses only

\[
L_{\hat{}}=1,\qquad\Gamma_{\hat{}}=1,
\]

plus dimensionless geometry, core ratio, amplitudes, time steps and target-free numerical controls. The source/payload guard rejects canonical SST constants, SI action columns and absolute targets from the blind dependency path.

## PKLSA provenance

PKLSA v0.1.0 contains 49 catalog families with 48 variants each, for 2352 candidates. Its release metadata explicitly states `topology_certified_by_atlas=false`: it is a constructive topology-preserving seed atlas, not an independent complete knot-invariant solver.

The embedded atlas is used as discovery geometry only. The v0.4.0 funnel never uses a Universal-Action result, \(h\), \(\hbar\), an SST mass relation, or a particle assignment to choose candidates. Public Stage-1/2 rows use salted opaque IDs; candidate/family identities and the materialized Stage-C mapping are quarantined under `private_reveal_keys` until reveal.

## GPU epistemic status

SYCL calculations are **screening only**. Stage 1 uses an instantaneous pair-distance strain diagnostic; Stage 2 uses a short RK2 invariant-shape/mesh diagnostic. Fixed per-family quotas prevent the approximate GPU score from deleting whole topology families before the trusted CPU stage.

A default SYCL production run is fail-closed unless GPU↔CPU-native parity passes. Regardless of parity, no GPU metric can issue the final scientific verdict: Stage 3 and Stage 4 use the C++/pybind11 CPU-double reference path.

## Reveal rule

The blind report may claim at most a **dimensionless numerical centerline Universal-Action candidate**. Absolute comparison to \(h\) or \(\hbar\) is post-reveal and remains `INDETERMINATE` unless the user supplies an independently sourced dimensional normalization whose provenance has no target ancestry.
