# Changelog

## v1.0.0

- Unified blind/multi-library, C++/pybind11 and SYCL audit infrastructure.
- Immutable create-once protocol freezing with per-file and bundle hashes.
- Gate dependency DAG enforcement; no out-of-order PASS.
- HMAC-SHA256 opaque IDs with private key rather than reversible public-salt hashing.
- Nonced reveal commitments.
- Mandatory blind-tree contamination scan, including `.tex`.
- Strict backend certification: requested/actual backend and authority must match.
- Build fingerprint contract includes source, Python ABI, pybind11, compiler identity and flags.
- Deterministic output ZIPs and clean-source checks.
- Added human/machine scientific contract and mandatory LaTeX falsifier report.
- Generated instances start `UNVALIDATED`; template validation never propagates as instance validation.
- External SYCL worker retained as a separate process; GPU FP32 is screening unless an instance explicitly preregisters otherwise.
