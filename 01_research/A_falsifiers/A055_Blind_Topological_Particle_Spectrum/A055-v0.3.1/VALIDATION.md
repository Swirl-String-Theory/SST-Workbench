# A055 v0.3.1 validation

**Release:** A055-v0.3.1  
**Framework:** SST Falsifier Framework **v1.0.4 CANONICAL_FROZEN**  
**Validation date:** 2026-10-07  
**Status:** **SOURCE / PROTOCOL VALIDATED — PRODUCTION PHYSICS NOT YET RUN**

## Canonical framework pin

A055 v0.3.1 was regenerated as a thin scientific instance of the frozen framework rather than patching the bespoke v0.3.0 runner forward.

- framework version: `1.0.4`
- framework status: `CANONICAL_FROZEN`
- canonical Workbench path: `06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.4`
- supplied canonical framework ZIP SHA-256: `1bdf8a20f0f0cbdf86ab89fb198d1930e0694579dee8d5dcd35149972c0d2104`
- framework package-manifest SHA-256: `1a9e98ee7762ab12746e5327a6552348d5e2edbee8ddaebc557ebaeb261e7452`
- A055 frozen protocol bundle SHA-256: `42d9419272431e6b43171e3a0cc67c3ed2d2700d6a16f76b5c05c69f5f395ace`

The canonical framework ZIP and package-manifest hashes were independently recomputed during release validation and matched the pin exactly.

## Framework and contract validation

- SST Falsifier Framework v1.0.4 selftests: **37 passed**.
- A055 public Python tests in the release environment: **8 passed, 1 skipped**.
- The skipped test is the instance-local pybind11 extension parity test because the release-validation container does not provide pybind11 and has no network access. `run_install.cmd` installs pybind11 before the target Windows selftest, and production G5 is fail-closed if the extension cannot build or meet parity.
- Python compile check: **PASS**.
- canonical science contract validation: **PASS**.
- canonical source contract validation: **PASS**.
- canonical gate-plan validation: **PASS**.
- canonical report-contract validation: **PASS**.
- public-source blind scan: **PASS**, zero forbidden-term hits.
- frozen protocol verification after assembly: **PASS**.

## Method-specific validation

The corrected directional statistic has analytic regression coverage for:

- positive and negative signed spatial harmonics;
- standing-wave rejection;
- conjugate-direction invariance;
- nonuniform arclength phase;
- periodic Bishop-frame orthonormality and closed-loop holonomy correction;
- eigenvalue-multiset assignment independent of ordering;
- rejection of an automatic complex-conjugate pair as a physical bidirectional pair;
- historical control-cell deduplication.

## Real sealed-upstream smoke

One anonymous candidate from the completed sealed A054 full campaign was recomputed at the sealed finest resolution using the portable NumPy reference path solely as an implementation smoke check.

- evaluated rows: **1**
- fine resolution: **88**
- sealed-spectrum maximum assignment-relative error: **4.298937913855639e-15**
- analytic signed-direction selftest: **PASS**
- positive-frequency projected modes: **21**
- qualified signed-travel harmonic entries under the final Bishop/Kelvin rule: **7**

This smoke is not a v0.3.1 scientific result and is not used to tune thresholds. The production FULL/CERTIFY campaign requires the sealed upstream backend class to match and must be executed on the target Workbench.

## Scientific changes validated in source

v0.3.1 corrects three known v0.3.0 analysis defects:

1. imaginary-eigenvalue sign is no longer treated as propagation direction;
2. historical mode/resolution cells are deduplicated by unique key rather than double-counting provider-level failure mirrors;
3. reveal-only component/architecture statistics are paired within frozen assignment/provider strata rather than using pooled unpaired medians as the primary identity comparison.

Additionally, v0.3.1 uses a periodic Bishop parallel-transport frame with distributed closed-loop holonomy correction and requires a majority Kelvin-family coefficient fraction before a mode can qualify as traveling.

## Production acceptance still required

On the user's Windows Workbench, `run_all.cmd full` must still demonstrate:

- completed sealed upstream discovery and control sources;
- exact upstream backend-class match;
- fine-resolution sealed-spectrum recomputation parity for the full registered population;
- instance-local C++17/OpenMP signed-harmonic parity at relative L2 `<= 1e-10`;
- framework BLIND packaging and gate ledger;
- separate commitment-verified REVEAL;
- deterministic BLIND, REVEALED and combined packages.

No v0.3.1 particle, compound, or mechanism conclusion is claimed by this source-validation document.
