# v1.0.10 local validation — 2026-10-19

- Base: exact clean v1.0.9 canonical ZIP, verified source manifest `104/104` and original manifest SHA-256 PASS.
- Full regression: **81 PASS** (72 inherited, 9 new gate execution/qualification/reveal tests).
- Generated-instance smoke: two sequential BASIC runs, two unique PDFs and blind ZIPs, archived previous output **PASS**.
- Generated-instance actual FULL diagnostic run: G2 FAIL, G3 PASS but DIAGNOSTIC_ONLY, G8 PASS but DIAGNOSTIC_ONLY; other enabled gates attempted; `REVEAL` preflight withheld; output manifest integrity **PASS**.
- Numerical C++/SYCL/DD32 kernels unchanged from v1.0.9; **no new target-machine hardware backend test in this environment**.
- Status: LOCAL_VALIDATED_CANDIDATE. Windows native `run_all.cmd ALL`, DD32 and both smoke scripts are required to promote the exact release ZIP to canonical.
- Technical limitations: cannot force arbitrary pre-existing custom instance pipelines to stop checking `dependencies_pass`; explicit migration is needed. Unknown exceptions remain fatal. Disabled and genuinely data-ineligible gates cannot be numerically evaluated.

## RC2 release-correction verification

- User's Windows candidate-1 evidence: 81 regression tests PASS, full C++/SYCL/DD32 parity PASS; DD32-only smoke PASS with C++ intentionally skipped; gate continuation and two-run retention smokes PASS.
- Candidate-1 has incorrect published version `1.0.9` in `pyproject.toml` and backend parity JSON. Fixes are version/provenance/display-only; no numerical kernels, accuracy gates or physics contracts are changed.
- This RC2 must be validated **as an exact new release artifact** before promoting to `CANONICAL_FROZEN`.

### Completed RC2 model-environment checks

- 83/83 Python regressions **PASS**.
- `pip wheel --no-deps --no-build-isolation` created `sst_falsifier_framework-1.0.10-py3-none-any.whl`.
- `smoke_non_short_circuit.py`: **PASS**. G2=FAIL; G3, G8=PASS with DIAGNOSTIC_ONLY; reveal rejected.
- `smoke_run_identity.py`: **PASS**. Two distinct run IDs, two PDFs, two ZIPs, original previous-run directory archived.
- Cross-platform/hardware repeat for the exact RC2 package: **PENDING**; prior candidate Windows parity is supporting but not exact-release evidence.

## Canonical promotion — Windows RC2 evidence, 2026-10-18/19

- `run_all.cmd ALL`: **83/83 Python regressions PASS**, C++/OpenMP FP64 PASS, Intel Arc A770 SYCL FP32 PASS, SYCL DD32 PASS, directional finite-difference stress PASS.
- Installed Python wheel metadata: **1.0.10**, replacing the erroneous first candidate's 1.0.9.
- `run_all.cmd DD32`: **PASS**. C++ correctly reported `SKIPPED (--skip-cpp)`, not a failure.
- Generated-instance non-short-circuit smoke: **PASS**; G2=FAIL, G3/G8=PASS but DIAGNOSTIC_ONLY, reveal ineligible.
- Two-run identity smoke: **PASS**; two unique PDFs, two unique BLIND ZIPs and previous output archived.
- Provenance caveat: Windows validation was performed by copying RC2 over the existing RC1 work directory, **not** using a cleanly extracted RC2 tree. The release source is instead constructed exclusively from the original manifest-verified clean RC2 ZIP.
- The Windows logs support tested core functionality and backend parity, not full independent Euler/PKLSA solver physics.
- Historical local candidate status earlier in this file is superseded by this explicit canonical promotion section; earlier test notes are retained for auditability.
