# VortexLab v7.6.25b — KnotPlot uniform-N300 catalog migration

Base: `vortexring-lab-v7.6.25a.html`

## Catalog migration

- Replaced the one-item legacy KnotPlot catalog with 11 runtime geometries: six classic knots, three `link_6.3.*` variants, `torus_3.3`, and `torus_6.9`.
- Migrated the active benchmark ID `Tlink_6_9` to `torus_6.9`. A one-way alias remains only for saved v7.6.25a selections/state.
- `torus_6.9` is validated as T(6,9): three T(2,3) components, expected pairwise `|Lk|=6`, status `relaxed-seed`, source normalization `D=1`, total source length `109.581016551918`.
- Candidate status distribution: {'near-ideal-candidate': 3, 'relaxed-seed': 8}. Family distribution: {'classic-knot': 6, 'link': 3, 'torus-link': 2}.

## Sampling correction

The new catalog stores full-spectrum coefficients that reconstruct the 300 source nodes. These coefficients are no longer interpreted as an independently certified smooth Fourier curve for KnotPlot tests.

- Dynamic/holdout route: reconstruct native N300 polygon → closed arc-length resample to the requested filament resolution.
- Reach route: periodic C2 spline through the native N300 polygon; the audit resolution controls the continuous search grid, not a different full-spectrum geometry.
- Ideal and compact Fseries routes remain unchanged.

## Benchmark changes

- Classic keys `3_1` through `7_1` now support Ideal + Fseries + KnotPlot triples.
- Added KnotPlot-only selectors for `link_6.3.1`, `link_6.3.2`, `link_6.3.3`, `torus_3.3`, and `torus_6.9`.
- The dedicated preset is now **Torus · T(6,9)**.
- All KnotPlot holdouts use the standard `a_sim=1.0 mm`; the obsolete D1/40k-specific `0.1 mm` exception was removed.
- Scenario exports now include candidate status/family, source role/SHA-256, D/L metadata, normalization, torus metadata, expected component count, and pairwise linking magnitude.
- Cross-embedding reports preserve the actual catalog status instead of hard-coding `relaxed-candidate`.

## Reach/DCSD changes

- G4a now requires every selected source/geometric ID to be represented, not merely one catalog result.
- Added G4b for KnotPlot uniform-N300 route and identity provenance.
- Added R42: `D=1` versus the discrete C2 reach proxy is reported as INFO only; it cannot certify physical diameter or global tightness.
- `torus_6.9` reach runs explicitly validate p=6, q=9, 3 components, and `|Lk|=6` metadata.

## Workflow and compatibility

- v7.6.25a saved `Tlink_6_9` selections migrate to `torus_6.9`.
- SPEC and decomposition completion may be inherited from the prior tab session; holdout, continuum, and reach unlocks are invalidated because their test definitions changed.
- Biot–Savart, RK4, topology guard, fixed-core limit, and velocity kernels are byte-identical to v7.6.25a.

## Required reruns

1. Select **Torus · T(6,9)** and run **Geselecteerde holdouts**.
2. Run **Continuüm N=128–768** to unlock reach in the enforced workflow.
3. Run **Continue reach/DCSD · Standaard** for `torus_6.9`.
4. Then use **Volledig · knopen + links** for the catalog-wide confirmatory reach audit when runtime permits.

A full interactive browser/WebGL run was not executed during packaging.
