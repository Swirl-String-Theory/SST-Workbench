---
name: PC00 certificate contract
todos:
  - id: t00
    content: "Define SST-SCIENTIFIC-CERTIFICATE-1.0 envelope (+ numerical_qualification, synthetic_inputs)"
    status: completed
  - id: t01
    content: "Generic promotable(cert) in 07_scripts; recompute promotion_allowed on write"
    status: completed
  - id: t02
    content: "Migrate A021/A038/A036 consumers to shared validator"
    status: completed
  - id: t03
    content: "Tests: SELFTEST reject; spoof reject; CAMPAIGN without numerical_qualification reject"
    status: completed
---
# PC00 — Scientific Certificate Hardening (contract 1.0)

Status: `DONE` · Priority: P0 · Risk: medium  
Depends on: [PU02b](PU02b_certificate_semantics.plan.md) (v1 DONE)  
Epic: [PRODUCTION_CERTIFICATION.plan.md](PRODUCTION_CERTIFICATION.plan.md)

## Closed 2026-09-08

- `07_scripts/paper_upgrade_certificate.py` — envelope, `promotable` / `promotion_eligible`, block codes
- `07_scripts/paper_upgrade_certs.py` — emit/write use envelope; `check-promotable` CLI
- A021 / A038 / A036 gates import shared validator
- On-disk A034/A037 certs rewritten as SELFTEST (`promotion_allowed=false`)
- A038 preflight on current certs → `BLOCKED_UPSTREAM_SELFTEST`
- Tests: **31 passed** (`test_paper_upgrade_certificate` + certs + 18 gates)

## Next

[PC01_d006_regression.plan.md](PC01_d006_regression.plan.md)
