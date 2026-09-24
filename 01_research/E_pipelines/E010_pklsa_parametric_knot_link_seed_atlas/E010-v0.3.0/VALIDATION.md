# Validation — E010 PKLSA v0.3.0

Package-level validation performed in the current runtime:

- Python compileall: PASS
- `tests/test_builder.py`: 15 passed, 0 failed
- optional PKLSA-v0.2.0 integration test: 1 passed, 0 failed
- `import sst_pklsa`: PASS

Not claimed here:

- full multi-GB SST-Workbench publication scan;
- native C++/pybind11 rebuild in this runtime;
- complete KnotInfo/LinkInfo XLS ingestion revalidation in this runtime.

The intended publication gate remains a local run of `run_all_publication.cmd` against the canonical SST-Workbench.
