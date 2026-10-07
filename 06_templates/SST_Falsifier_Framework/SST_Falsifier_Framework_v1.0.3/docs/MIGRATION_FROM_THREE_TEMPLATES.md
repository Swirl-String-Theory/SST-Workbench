# Migration from the three legacy templates

| Legacy responsibility | v1.0.3 destination |
|---|---|
| Blind protocol, source discovery, gates | `sst_falsifier/protocol.py`, `blind.py`, `gates.py`, `source_registry.py` |
| pybind build/fallback | `native_build.py` + instance-local `native/cpp/native.cpp` |
| SYCL worker | `sycl_worker.py` + instance-local `native/cpp/sycl_worker.cpp` |
| Output ZIPs | `outputs.py` deterministic archives |
| Validation docs | instance `VALIDATION.md` starts UNVALIDATED |
| Scientific explanation | mandatory `report/FALSIFIER_REPORT.tex` + `science_contract.json` |

Do not copy generated `.pyd/.lib/.exp/.exe`, caches, or old output trees into the framework. Build artifacts belong to the local `build/` and are fingerprinted.
