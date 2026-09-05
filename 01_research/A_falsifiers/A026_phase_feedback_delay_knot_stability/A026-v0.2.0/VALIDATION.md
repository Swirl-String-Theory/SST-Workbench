# Validation — SST Phase-Feedback Delay Knot Stability Blind Falsifier v0.2.0

Validated in the artifact environment:

- Python regression suite: **12 passed**.
- Preregistration lock: **PASS** for docs, both frozen configs, historical registry, scientific Python modules, and C++ kernels.
- v0.1.7 real matrix preview: **41 source files -> 10 unique identity128 geometries -> 31 duplicates removed -> 10 historical seen -> 0 novel**.
- Legacy preparation on the same real matrix: **10 blind unique candidates**, no pseudoreplication.
- Confirmatory preparation on the same real matrix: **0 selected candidates**, correctly preventing reuse as a new confirmatory campaign.
- Synthetic packet centroid transport fit recovers the prescribed group velocity.
- Synthetic strict negative delay/growth signal passes both v0.2 physics gates.
- Duplicate blind-manifest invariant violation produces `INCONCLUSIVE`.
- Self-test with the Python backend: **PASS**.

The C++ scientific kernels are unchanged from the v0.1.7 code path that passed the user's Windows MSVC native/Python parity test; they are included in the v0.2 preregistration lock. The artifact environment could not rebuild pybind11 because internet/package retrieval is unavailable here, so the final native build must still be exercised by `run_00_install.cmd` on the Windows target.
