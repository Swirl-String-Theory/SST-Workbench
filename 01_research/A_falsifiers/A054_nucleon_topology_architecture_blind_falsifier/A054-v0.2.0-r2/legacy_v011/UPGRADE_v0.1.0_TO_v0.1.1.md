# Upgrade v0.1.0 -> v0.1.1

Major changes:

1. Replaces the six named proton/neutron hypothesis cells with a full `3 skeleton x 2^3 twist assignment` factorial design.
2. Adds prospective `2+1` polarity selection gates under both circulation normalizations.
3. Adds reveal-only single-site `5_2 -> 6_1` contrasts and polarity-by-opposed-knot interaction analysis.
4. Adds dimensionless mutual-filament interaction energy and finite-difference component-separation diagnostics.
5. Repairs dynamics convergence: fixed final time with `dt ~ N^-2`; dynamic observables now participate in spatial convergence.
6. Adds optional finest-grid temporal refinement; required in `extended`.
7. Repairs native/reference validation with explicit NumPy and native code paths.
8. Seals backend qualification and exact config hash with the blind outputs.
9. Renames `SURVIVES_BLIND_SCREEN` to `NUMERICALLY_QUALIFIED` to prevent scientific over-interpretation.
10. Fixes BLIND archive packaging: `_private` is excluded and archive contents receive their own SHA-256 manifest.
11. Freezes the v0.1.0 discovery provenance in `data/V010_DISCOVERY_PREREGISTRATION.json`; its numerical effect sizes are not v0.1.1 scoring inputs.
