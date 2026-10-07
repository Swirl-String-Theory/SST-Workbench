# SST Falsifier Framework v1.0.0 — Validation Record

Validation date: 2026-10-06

## Verified in this release environment

- Python framework test suite: **21 / 21 PASS**.
- Generated `FALSIFIER_REPORT.tex`: compiled successfully with `pdflatex` to a 7-page A4 document.
- Create-once preregistration: a changed frozen protocol is rejected rather than overwritten.
- Gate-DAG enforcement, including transparent handling of `NOT_APPLICABLE` dependencies.
- HMAC-SHA256 opaque identifiers with a private key.
- Nonced commitments for the private forbidden-term list and reveal payload.
- Blind contamination scanning, including `.tex` and ordinary public output files.
- Deterministic ZIP generation and source-release contamination checks.
- Strict backend authority: a Python fallback cannot satisfy a C++ certification gate.
- End-to-end blind -> FULL -> REVEAL lifecycle using the reference/example pipeline.
- REVEAL blocking when blind prerequisites are unresolved.
- Reveal commitment verification and generation of a separate revealed gate ledger.
- Generated instances start `UNVALIDATED`; validation state is not inherited from the framework template.

## Structurally validated but not hardware-executed here

- C++/pybind11 native extension build path. The execution environment used for this release does not contain `pybind11`, and network access is disabled, so a fresh native compilation was not claimed as tested.
- Intel oneAPI/DPC++ SYCL worker on an Intel Arc GPU. The worker protocol, source, build-fingerprint logic, work guard, precision/authority metadata, parity contract and timing fields were inspected/tested at framework level, but no Intel Arc/SYCL device is available in this release environment.

These two lanes therefore remain **environment-dependent certification checks**. A scientific instance that preregisters C++ or SYCL as required must execute those checks on the target machine; the framework must not convert an unavailable required backend into a certification PASS.

## Release criterion

The source release is acceptable only if `tools/check_release_clean.py` reports no generated binary/cache contamination and the package manifest matches the distributed source tree.
