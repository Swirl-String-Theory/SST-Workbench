# PC00 Report — Scientific Certificate Hardening (2026-09-08)

**Verdict:** DONE — 31/31 tests PASS. On-disk A034/A037 certs are SELFTEST and not promotable. A038 preflight reports `BLOCKED_UPSTREAM_SELFTEST`.

## What landed

| Artifact | Role |
|----------|------|
| `07_scripts/paper_upgrade_certificate.py` | `SST-SCIENTIFIC-CERTIFICATE-1.0`, `promotable()`, block codes |
| `07_scripts/paper_upgrade_certs.py` | emit/write + `check-promotable` |
| A021 / A038 / A036 `paper_upgrade/gate.py` | shared `require_promotable` |
| Rewritten `outputs/basic/paper_upgrade/certificate.json` | A034 + A037 |

## `promotable(cert)` rule

```text
certificate_kind == CAMPAIGN
AND scientific == true
AND status == PASS
AND synthetic_inputs == false
AND numerical_qualification.{temporal,spatial,mesh} == PASS
AND stamped promotion_allowed == true   # recomputed on write; spoof-safe
```

## Key results

### Pytest

```text
31 passed in ~5s
```

(see `logs/pytest_pc00.log`)

### check-promotable (on-disk)

```json
{"promotable": false, "reason": "not-campaign", "blocked": "BLOCKED_UPSTREAM_SELFTEST"}
```

for both A034 and A037.

### A038 preflight vs current campaign outputs

```json
{
  "downstream_authorized": false,
  "primary_block": "BLOCKED_UPSTREAM_SELFTEST",
  "block_codes": [
    "geometry:BLOCKED_UPSTREAM_SELFTEST",
    "mesh:BLOCKED_UPSTREAM_SELFTEST",
    "admissibility:BLOCKED_UPSTREAM_SELFTEST",
    "symmetry:BLOCKED_UPSTREAM_SELFTEST"
  ]
}
```

→ **not** `FAIL_TREFOIL`.

## Zip contents

- This report
- Plans (PRODUCTION_CERTIFICATION, PC00–PC05, README, TOTAL_REPORT)
- `logs/` — terminal captures (pytest, selftests, emit, preflight)
- `results/` — D006/C006/A037/A034 outputs + rewritten certificates + heartbeats

## Next

PC01 D006-v0.4.1 regressions → PC02 A037-v0.3.1.
