# Validation — SST Trefoil Dynamic Seed Qualification Mega Falsifier v0.3.0

Date: 2026-08-30

## Supplied Codex v0.2.2 evidence audit

- Outer delivery SHA-256: `eb13ee60e3f423cb77907661a2bc5fd94a3b851fe6185937beba50b3f551d5f5`.
- Nested code/evidence ZIP SHA-256: `78bd588922747db8221567d0758181114377d1aca8db99fa63cb6741cd120744`.
- Nested `MANIFEST.json`: 73/73 entries independently re-hashed; 0 mismatches.
- Historical scientific status supported by the supplied machine-readable summaries:
  resolution/temporal/core produced 4 qualified candidates, S37 mesh-gauge produced 0/4,
  and no eligible S40-S60 / trefoil Phase-B result followed. Physics verdict remains
  `INDETERMINATE`.
- Supplied package version metadata was internally inconsistent (0.2.0/0.2.1/0.2.2).
  v0.3.0 introduces a single release identity.

## SST Knot Library dependency

A v0.2.5 provenance hotfix was created before integration because `Fremlin_FourierSeries`
would otherwise be classified as KnotPlot fseries by the v0.2.4 path heuristic.

SST Knot Library v0.2.5 local validation:

- Python tests: 27/27 PASS.
- Standalone C++17/OpenMP self-test: PASS.
- Release manifest: 62/62 PASS.
- Reference validation reports library version 0.2.5.
- Fremlin `.short` is classified as `fremlin_short_coordinate` with provider
  `fremlin_local_fourier`, never KnotPlot.
- `.fseries` coefficient semantics are still not guessed.

## Falsifier v0.3.0 validation

With `SST_KNOT_LIBRARY_HOME` pointing to the validated v0.2.5 release:

- `compileall`: PASS.
- pytest: 55/55 PASS.
- Pinned dependency activation: PASS.
- Fremlin source-provider regression: PASS.
- Release identity test: PASS.
- Existing v0.2.2 numerical/phase-boundary tests preserved and PASS.

### End-to-end pre-dynamics trust-boundary test

A temporary repository layout was populated with trefoil integration fixtures and the
exact v0.2.5 library. The following chain was executed:

`atlas freeze -> atlas generate-test -> KnotRecord recomputation -> blind candidate prepare`.

Observed:

- atlas status: `QUALIFIED_PROSPECTIVE_REALIZATION_ATLAS`;
- KnotRecord binding: PASS;
- 3 source-family groups;
- 6 generated test realizations;
- 6 blind prepared candidates;
- prepare verdict: `PASS_SOURCE_STRATIFIED_PREPARE`;
- public evidence contains the pinned KAtlas/source-catalog/release/manifest attestation.

This test validates input/provenance plumbing only; it is not physics evidence.

## Native backend note

The v0.3.0 release does not redistribute the stale Windows `.pyd` from the supplied Codex
bundle. `run_01_build_native.cmd` rebuilds the extension locally from unchanged C++ source.
The present Linux container lacks `pybind11`, so the new native extension was not rebuilt
here. The supplied v0.2.2 evidence included a Windows CPython 3.14 native binary and reported
its selftest as PASS; v0.3.0 does not alter `cpp/native.cpp`. The user's Windows
`run_all_atlas.cmd` run is therefore the decisive v0.3.0 native/MSVC validation.

## Scientific non-claims

v0.3.0 does not convert a KAtlas reference into geometry certification, does not make the
three construction lineages statistically independent observations, does not relax S37,
and does not turn the historical v0.2.2 `INDETERMINATE` result into an SST confirmation or
falsification.
