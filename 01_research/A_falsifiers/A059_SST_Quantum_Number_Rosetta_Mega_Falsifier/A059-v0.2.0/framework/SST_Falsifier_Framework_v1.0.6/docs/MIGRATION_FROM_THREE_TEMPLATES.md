# Migration from the three legacy templates

| Legacy responsibility | v1.0.6 destination |
|---|---|
| Blind/multi-library commitments and packaging | `sst_falsifier/blind.py`, `protocol.py`, `outputs.py`, `runner.py` |
| C++/pybind build + certification | `sst_falsifier/native_build.py`, `backends/cpp_pybind.py` |
| GPU/SYCL worker + DD32 | `sst_falsifier/sycl_worker.py`, instance-local `native/cpp/sycl_worker.cpp` |
| Gate DAG | `sst_falsifier/gates.py` |
| Independent replication semantics | `sst_falsifier/replication.py` |
| Scientific/report contract | `science_contract.py`, `report.py`, `instance_template/report/` |
| Framework discovery/pinning | instance-local `framework_bootstrap.py` |
| Package-safe custom launcher | instance-local `run_python.py` + `run_python.cmd` |
| Reveal preflight/integrity | `runner.reveal_eligibility()`, exact output manifest verification |

Historical falsifiers remain pinned to their original framework/template. Migrate only when creating a new falsifier version or when an explicit migration is scientifically justified.
