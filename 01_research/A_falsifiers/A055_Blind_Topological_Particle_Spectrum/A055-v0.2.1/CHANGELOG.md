# Changelog

## v0.2.1 — 2026-10-06

Focused repair release after the first A055 v0.2.0 production campaign.

1. **XYZ provider support**
   - `source_locator.representation == "xyz"` is now a first-class one-component knot carrier.
   - Whitespace/comma-separated XYZ, comments, optional headers, and duplicate closing points are handled.
   - The same E011 ropelength normalization and orientation contract is applied as to Gilbert/VECT sources.

2. **Missing-provider status instead of loader failure**
   - A STATIC_READY topology with only one preregistered provider is reported as `SINGLE_PROVIDER_ONLY`.
   - Its available provider may run Kelvin/RPO diagnostics.
   - It cannot pass cross-provider agreement, true particle-promotion, or enter the SM mass-pattern fit.
   - Ambiguous duplicate anchors still fail closed.

3. **Hard C006 native gate**
   - Production `quick`/`full` campaigns require C006's native backend to build/import as `cpp`.
   - A deterministic native-vs-Python `pair_rhs` parity test runs before BLIND data are generated.
   - Production aborts if native import or parity fails; silent Python fallback is forbidden.

Additional provenance fix:
- quick outputs: `...v0.2.1-quick-outputs`
- full outputs: `...v0.2.1-full-outputs`
- CI outputs: `...v0.2.1-ci-outputs`

This makes campaign identity visible in both the frozen config and filesystem name.
