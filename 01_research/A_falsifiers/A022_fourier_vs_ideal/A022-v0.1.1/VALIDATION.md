# v0.1.1 MSVC hotfix validation note

The v0.1.1 change is source-portability only. The Windows failure reported under MSVC 14.44 / CPython 3.14 starts at unqualified `ssize_t`; the later parser/type errors are cascading diagnostics. All unqualified `ssize_t` occurrences have been removed from the native source. Python regression tests are rerun unchanged.

# Validation — v0.1.1

Validation date: 2026-08-20.

## Static / Python

- Python syntax compilation: **PASS**.
- Unit tests: **12/12 PASS**.
- Coverage includes arclength resampling, rigid/cyclic alignment, tangential-gauge quotienting, exact segment contact distance, source-ID normalization, Fremlin six-column parsing, infinite-metric handling, exact binomial tail, and catalog-tree hashing.

## Native C++17 / pybind11

- `cpp/native.cpp` C++17/OpenMP syntax check: **PASS**.
- Native extension compilation/load against an available pybind11 header set: **PASS**.
- Backend reported `cpp-pybind11`: **PASS**.
- 48-point ring velocity finite: **PASS**.
- Exact non-adjacent segment-gap kernel finite: **PASS**.

The v0.1.1 translation unit was compiled and loaded manually against available pybind11 headers and all native smoke tests passed. This environment does **not** provide MSVC, so the exact MSVC 14.44 rerun cannot be certified here; v0.1.1 specifically removes every unqualified `ssize_t` occurrence that caused the supplied Windows parse failure. On Windows, `run_00_install.cmd` installs `pybind11` before `run_01_build_native.cmd` invokes the normal setup route.

## Real-source ingestion

Using the actual Fremlin archive and the VortexLab/Gilbert `ideal_knots_data.js` source:

- Gilbert/VortexLab entries parsed: 31.
- Canonical Fremlin `.fseries` entries parsed: 27.
- Matched one-component knot IDs: **13**.
- Current matched torus subset: **`3_1`, `5_1`, `7_1`**.
- Catalog ID normalization `3:1:1 -> 3_1`, `10:1:124 -> 10_124`: **PASS**.

A reduced two-pair real-source campaign completed end-to-end with the native backend:

```text
prepare       13 pairs / 26 anonymous candidates
blind run     2/2 valid (validation limit=2)
seal          SEALED
reveal verify PASS
```

This reduced campaign is a pipeline smoke test only; its scientific scores are not evidence for either source family.

## Tamper test

After sealing, one byte was appended to an anonymous geometry `.npz`. Reveal was rejected with:

```text
anonymous public geometry/catalog changed after seal
```

Tamper rejection: **PASS**.

## Scope limits

- The filament model is a VortexLab-style local-induction + nonlocal Biot--Savart discretization, not a proof of full Euler/GP/SST stability.
- `rpo_residual` is a recurrence proxy, not a Newton-refined RPO certificate or true Floquet monodromy.
- The three-pair torus stratum is statistically underpowered by itself: even 3/3 same-direction wins gives one-sided exact sign-test `p=0.125`. The 13-pair all-knot campaign is therefore the primary aggregate source test; the torus result remains a separately reported stratum.
