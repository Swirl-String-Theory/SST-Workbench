# Changelog

## v0.1.1
- Narrowed the convergence campaign to `q=2.31..4.10`, respecting the exact geometric non-overlap bound for the default ring.
- Added independent node ladder `N=32,48,64,96`.
- Added image-shell ladder `1,2,3`.
- Added finite-difference ladder `3e-4,1e-4,3e-5,1e-5`.
- Added automatic local refinement of every primary coarse-grid candidate to `Delta q=0.0025`.
- Added full eigenvector branch tracking using phase-invariant overlap.
- Added computed finite-difference roundoff floor and a fixed 100x signal gate for neutral-subspace candidate nomination.
- Added cross-ladder candidate clustering and preregistered convergence gates.
- Added baseline-result caching across ladder axes.
- Added `freeze_results.py` for SHA-256 freezing before any external comparison.
- Updated Windows `run_full.cmd`, `run_quick.cmd` and `run_refinement.cmd`.

## v0.1.0
- Initial blind dimensionless finite-core periodic-ring spectral selector.
