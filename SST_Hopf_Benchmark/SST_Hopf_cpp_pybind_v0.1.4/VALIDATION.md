# Validation — SST Hopf C++/pybind Benchmark Pack v0.1.4

## Scope

v0.1.4 is primarily a **blind-campaign and orchestration release**. It does not change the v0.1.3 Hopf/Hodge mathematics. The native C++ numerical kernels are unchanged except for the backend version string.

## Static checks

- Python syntax compilation for all root/package scripts: **PASS**.
- Blind configuration guard: **PASS**.
- Candidate metadata leakage guard: **PASS**.
- Result-tree sealing and verification: **PASS**.
- Candidate-key pre-commit verification: **PASS**.

## Blind workflow smoke test

A reduced reference-mode campaign was run end-to-end:

```text
prepare anonymized candidates   PASS
blind H0-H4                     PASS
H5 identity self-test           IDENTITY_BENCHMARK_PASS / excluded from physical evidence
H9 double-cover self-test       INDETERMINATE / kinematic-only
anonymous candidate analysis    PASS
blind summary                   sst_inputs_used=false
blind summary                   target_values_used=false
blind summary                   candidate_identity_read=false
seal                            SEALED
post-seal reveal verification   PASS
```

The reveal smoke test produced the expected epistemic separation:

```text
carrier knot identity     CATALOG_IDENTIFICATION_ONLY
Hopf comparison           MATCH
helicity ratio            NOT_IDENTIFIABLE_FROM_BLIND_PHYSICAL_DATA
spin sector               NOT_IDENTIFIABLE_FROM_BLIND_DATA
4pi                       KINEMATIC_MATCH_ONLY
```

This validates software semantics only. The validation reveal used a synthetic validation model, not an SST result claim.

## H10 orchestration regression

The ordinary QUICK H0-H10 chain was rerun in Python-reference mode after the wiring patch.

Step 8 now receives upstream evidence and reports:

```text
H1   PASS
H3   PASS
H5   DEMONSTRATION
H6   DEMONSTRATION
H7   INDETERMINATE
H8   INDETERMINATE
H9   INDETERMINATE
```

with all seven upstream sources marked available.

Therefore the previous `MISSING` values caused by runner orchestration are repaired. H10 correctly remains `INDETERMINATE`.

## Native status

The user's v0.1.3 Windows run already established the C++17/pybind backend on CPython 3.14.3/pybind11 3.1.0. v0.1.4 does not add a new numerical C++ kernel; it only bumps the native backend version string and reuses the v0.1.3 kernels.

This execution environment still lacks a locally installed pybind11 development package, so a v0.1.4 Windows-native rebuild cannot be reproduced here. The authoritative local commands are:

```cmd
RUN_ALL.cmd
RUN_BLIND_ALL.cmd
RUN_BLIND_CONVERGENCE.cmd
```

## Dependency contract

Still explicit:

```text
numpy>=2.0
pybind11>=2.13
setuptools>=68
wheel>=0.43
```

## Production blind default

`blind_config.json` uses:

```text
Hopf resolutions        48,64,96,128
candidate samples       900
toroflux grid           96
fiber samples           1200
save level              evidence
```

`save_level=evidence` removes heavy result NPZ checkpoints after extracting the evidence, so the default blind campaign does not accumulate the very large field archives seen in exploratory runs.
