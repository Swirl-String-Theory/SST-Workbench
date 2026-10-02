---
name: PC01 D006 regression
todos:
  - id: t00
    content: "Bump D006-v0.4.0 → v0.4.1 harness package + project.json"
    status: pending
  - id: t01
    content: "Test A: parity-perfect + CFL invalid → mirror PASS, science INVALID, no promotion"
    status: pending
  - id: t02
    content: "Test B: SELFTEST+PASS certificate → promotion REJECT"
    status: pending
  - id: t03
    content: "Test C: f_proj≪1 → Hessian PASS must not auto-promote"
    status: pending
---
# PC01 — D006 v0.4.1 certificate / numeric regression

Status: `PLANNED` · Priority: P0 · Risk: low  
Depends on: [PC00](PC00_certificate_contract.plan.md)  
Epic: [PRODUCTION_CERTIFICATION.plan.md](PRODUCTION_CERTIFICATION.plan.md)

Encode what the first campaign revealed as **synthetic regression cases** (not new physics).

Live tip: `D006-v0.4.0` → target **`D006-v0.4.1`** (proposal’s v0.3.1 maps to this tip).

## Test A — parity-perfect but numerically invalid

Construct \(Q_B=-Q_A\) exactly with e.g. \(\mathrm{CFL}=5\).

Expected:

```text
DISCRETE_OPERATOR_MIRROR_COVARIANCE = PASS
PHYSICAL_TRAJECTORY_SYMMETRY_RESPONSE = INVALID_NUMERICS
promotion_allowed = false
```

## Test B — fake selftest certificate

```text
SELFTEST + status PASS-looking → promotion REJECT
```

## Test C — weak reduced manifold

With \(f_{\mathrm{proj}}=0.002\), a favorable local Hessian must **not** yield candidate promotion
(`REDUCED_MANIFOLD_BREAKDOWN` / non-promotable).

## Done-criteria

Harness selftest + these three cases PASS in CI/local `run_all` / dedicated pytest.

## Next

[PC02_a037_v031.plan.md](PC02_a037_v031.plan.md)
