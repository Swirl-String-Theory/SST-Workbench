# Validation status — v0.2.2

Certification-only hotfix over v0.2.1. Scientific configs, blind salts, equations, gates, frozen seeds, and thresholds are unchanged.

Validated in this release build:

- [x] Python unit tests: **11/11 PASS**.
- [x] Regression: generated `certification/leakage_audit.json` cannot self-contaminate G0.
- [x] Regression: native `build/.../native.obj` cannot contaminate G0.
- [x] Positive control: forbidden token in allowlisted blind source fails G0.
- [x] Empty audit surface fails closed.
- [x] Python smoke campaign with BLIND and REVEALED packaging.
- [x] Frozen input SHA-256 gate.
- [x] G0 positive-allowlist audit: **PASS**, 18 files scanned, 0 hits, 0 read errors.
- [x] v0.2.1 -> v0.2.2 Python smoke scientific parity: `blind_metrics.csv` and blind seed descriptors are byte-identical; G1-G7 values are exactly identical.
- [x] `configs/smoke.json`, `configs/basic.json`, and `configs/extended.json` are byte-identical to v0.2.1.
- [ ] Native C++17/pybind11 build on the release host: not run because `pybind11` is unavailable in this container. The user's preceding Windows v0.2.1 run compiled/linked the unchanged native equations and completed the native basic campaign before G0 certification failed.
- [ ] Independent v0.2.2 Python/native parity basic campaign.
- [ ] Extended finite-core ladder campaign.
- [ ] Certified RPO supplied upstream before any Floquet multipliers are evaluated.

Config SHA-256 values retained from v0.2.1:

```text
smoke.json     861bd0b7325604c9a4edd911484117928a7a6b2205a7730c4f99b6cad273607c
basic.json     319603a432e015b4489f18d81c63d00eadb71610479f5db95b3da92d966802ef
extended.json  35ee5b3f6e2fb56ce84dc5e28f565166019fe74c8ba8a95cd12de9ba994c1219
```

Trigger evidence: the user-provided native Windows v0.2.1 BLIND run had G1-G7 PASS but G0 FAIL due only to generated `certification/leakage_audit.json` and `build/.../native.obj` entries. v0.2.2 fixes that certification surface definition without converting the numerical result into a physics verdict.
