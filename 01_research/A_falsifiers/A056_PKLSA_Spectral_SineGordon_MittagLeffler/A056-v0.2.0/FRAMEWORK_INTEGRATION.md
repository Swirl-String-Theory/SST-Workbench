# First consumer test of SST Falsifier Framework v1.0.0

A056 v0.2.0 is deliberately structured as the first integration test of the in-development framework rather than as another standalone falsifier with duplicated infrastructure.

## Framework pieces exercised

| Framework concern | A056 v0.2.0 use |
|---|---|
| protocol / gate order | dependency-checked G0--G6 ledger |
| blindness | private reveal commitment + source-tree scan |
| provenance | input/config/environment hashes and provider IDs |
| sources | strict dynamic-provider metadata contract |
| outputs | canonical local output directory + BLIND/REVEALED packages |
| C++/pybind audit | separate C++17/OpenMP native kernel + Python reference |
| GPU/SYCL audit | out-of-process oneAPI worker probe, screening only |
| reproducibility | deterministic 2x resolution certification |
| report template | mandatory `.tex` audit report describing equations, code path, gates and results |

The bundled `sst_falsifier_framework` package is marked `1.0.0.dev0`, not final `1.0.0`. It is an integration snapshot so this falsifier can exercise the proposed API before the framework is frozen. When the canonical framework lands in the Workbench, the correct next step is to diff this consumer against it and remove the vendored snapshot rather than silently maintaining two frameworks.

## Important framework test

A056 tests a useful failure mode: a model can win discovery yet fail held-out confirmation; or pass scientific fitting but remain `UNRESOLVED` because native parity / resolution certification fails. The dependency-aware ledger prevents those intermediate states from being promoted to a physics PASS.
