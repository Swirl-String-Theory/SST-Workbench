# Validation

- Python syntax compilation: **PASS**
- Low-resolution end-to-end smoke test: **PASS**
- Evidence JSON files validated: **8/8**

The smoke test intentionally reports:

- H5 as `DEMONSTRATION` when velocity/vorticity are constructed from the Hopf connection;
- H6 as `DEMONSTRATION` and H7/H8 as `INDETERMINATE` for synthetic action data;
- H9 as `INDETERMINATE` without a configuration-space certificate;
- H10 as `INDETERMINATE` without independent knot and upstream gate evidence.

These statuses are deliberate epistemic guards, not software failures.
