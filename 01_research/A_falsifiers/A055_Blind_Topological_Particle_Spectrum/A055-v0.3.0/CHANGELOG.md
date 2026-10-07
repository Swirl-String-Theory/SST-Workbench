# Changelog

## v0.3.0 — 2026-10-07

Major compound-integration release.

- Audits A054 v0.1.1/v0.2.x rather than duplicating its three-component solver.
- Adds an A054 sealed-campaign bridge as authoritative multi-component C-branch.
- Retains A055 single-knot C006 dynamics only as S-branch controls.
- Adds per-(provider,N,m) failure bookkeeping: one missing counter-propagating pair no
  longer deletes all other mode/resolution evidence for a topology.
- Adds full-spectrum and Kelvin-restricted counter-propagating-pair diagnostics.
- Adds frozen frequency-symmetry diagnostic \(A_\omega\le0.25\).
- Adds blind 2+1-vs-+++ and linked-vs-unlinked categorical bridge outputs.
- Adds reveal-only opposed-knot identity analysis.
- Adds reveal-only working proton-like `G(5_2,5_2,6_1)` and neutron-like
  `B(5_2,6_1,6_1)` reports.
- Explicitly forbids raw spectral pooling between the S and C branches.
- If no sealed A054 certification is available, production can invoke the authoritative
  A054 v0.2.x campaign instead of reimplementing its physics.
