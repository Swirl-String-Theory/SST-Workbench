# Validation Report — v0.1.0

Date: 2026-08-01

## Automated checks

- Python syntax compilation: **PASS**
  - `src/sst_dimensionless_ratios.py`
  - `src/sstcore_bridge.py`
- Pytest: **4/4 PASS**
- Ring self-test: **PASS**
- JSON parse validation: **PASS**
- Markdown/Python control-character scan: **PASS**
- Quick campaign: **PASS**
- Deterministic replay hash: **PASS**
- Wheel build with local build environment: **PASS**
- Wheel install/import/self-test in isolated target directory: **PASS**

The quick campaign `campaign_results.json` reproduced byte-for-byte with SHA-256:

```text
b82a70ef8e5090a8fa342d1001c77e0566463e265d86b1be5b00352ac498016e
```

## Unit tests

1. fixed-length ring normalization and relative-equilibrium residual;
2. ideal-AB parser and mirror-trefoil energy parity;
3. finite velocity under all three core kernels;
4. recurrence invariance under cyclic parametrization shift.

## Quick-campaign qualitative result

- ring: relative-equilibrium residual at numerical roundoff;
- trefoil: residual approximately `0.215`;
- mirror trefoil: same parity-even static energy and residual;
- figure-eight: residual approximately `0.43–0.44`;
- short-time energy drift remained small for the ring and sub-percent to percent-level for the non-equilibrium knot inputs;
- no dominant-frequency claim was emitted because the smoke-test time series is too short.

## Validation scope

These checks establish software reproducibility and internal numerical sanity only. They do not establish:

- continuous finite-core Euler correctness;
- exact reach or ropelength certification;
- periodic-orbit existence;
- Floquet or KAM stability;
- regulator independence;
- particle ontology;
- agreement with experiment.
