# Validation status — A055 v0.1.1

Validated in the artifact environment on 2026-10-06.

## Passed checks

- Python source compilation (`compileall`): PASS.
- Python reference self-test: PASS.
- Atlas cardinality: PASS (35 knots + 47 links = 82).
- PD traversal/component tests: PASS, including knot, 2-component, 3-component and 4-component examples.
- Feature-domain regression: PASS.
  - `linking_strength` ratio pool is links-only.
  - mixed `abs_writhe` is forbidden.
  - `contact_ratio` is diagnostic-only.
- Exact null-envelope acceleration vs brute force on a deterministic test cache: PASS to \(10^{-10}\) absolute tolerance.
- End-to-end 82-case Python CI campaign: PASS (`blind -> seal -> reveal -> package`).
- End-to-end 82-case Python CI campaign with **10,000 null trials per valid search**: PASS.
- Nested familywise null aggregation (common-all, all valid domains, and global across registered SM groups): PASS.
- 10,000-trial reveal path completed in the artifact environment without brute-force null rescanning; full compressed null distributions were generated.
- Recursive BLIND SHA-256 seal verification after reveal: PASS.
- BLIND leakage scan: PASS for `5_2`, `6_1`, charged-lepton labels, `Higgs`, and representative reveal-only mass values.
- Feature-domain output audit: PASS; `linking_strength` knot/mixed searches and mixed `abs_writhe` are emitted as `INVALID_FEATURE_DOMAIN`.
- C++ source MSVC portability audit: explicit `constexpr` \(\pi\), C++17, pybind11 and OpenMP configuration present.

## Native compilation limitation in this artifact environment

The artifact runtime does not contain `pybind11`, and outbound package installation is unavailable.  Therefore the C++ extension could not be compiled here.

This does **not** silently downgrade the normal Windows workflow: both `basic.json` and `full.json` set `strict_native=true`, and `run_all.cmd` performs the C++ build plus Python/C++ numerical parity test before starting the blind campaign.  `run_python.cmd` is explicitly a diagnostic fallback.

## CI preset

`configs/ci.json` is included only for fast software regression testing.  Its low resolutions, two replicates, relaxed gates and 100 nulls are **not** valid scientific campaign settings.  Scientific screening should use `basic` or preferably `full`.

## Historical v0.1.0 regression basis

The uploaded first-run archives used to motivate this patch were independently SHA-256 checked during patch development.  Their preserved hashes and methodological postmortem are documented in `docs/V0_1_0_POSTMORTEM.md`.
