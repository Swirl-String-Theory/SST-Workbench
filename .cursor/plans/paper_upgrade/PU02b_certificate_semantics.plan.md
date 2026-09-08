---
name: PU02b certificate semantics
todos:
  - id: t00
    content: "Schema fields: certificate_kind, scientific, promotion_allowed (+ hashes)"
    status: completed
  - id: t01
    content: "Synthetic emit → SELFTEST / scientific=false / promotion_allowed=false"
    status: completed
  - id: t02
    content: "Consumers (A021/A038/A036 + wrappers) reject unless promotion_allowed"
    status: completed
  - id: t03
    content: "Rewrite existing A034/A037 on-disk certs; update tests"
    status: completed
  - id: t04
    content: "Done-criteria: synthetic cannot authorize downstream; CAMPAIGN path documented"
    status: completed
---
# PU02b — Certificate production semantics (no synthetic promotion)

Status: `DONE` · Priority: P0 · Risk: high · Depends on: [PU02](PU02_certificate_adapters.plan.md)  
Epic: [PAPER_UPGRADE_EPIC.plan.md](PAPER_UPGRADE_EPIC.plan.md)

## Why

PU02 proved the emit/consume **pipeline** with synthetic fixtures. Those fixtures previously
wrote `status: PASS`, so A038/A021 could treat them as scientific green lights.

## Rule

\[
\texttt{promotion\_allowed}
=
(\texttt{scientific}=\texttt{true})
\land
(\texttt{certificate\_kind}=\texttt{CAMPAIGN})
\land
(\texttt{status}\in\{\texttt{PASS},\texttt{QUALIFIED}\})
\]

## Closed 2026-09-08

- `07_scripts/paper_upgrade_certs.py` — `apply_certificate_semantics`, spoof-resistant `write_certificate`
- Synthetic CLI → `SELFTEST` / `PIPELINE_PASS` / `promotion_allowed=false`
- A021 / A038 / A036 consumers enforce CAMPAIGN + `promotion_allowed`
- On-disk A034/A037 certs rewritten
- Tests: `test_paper_upgrade_certs.py` + gate suite **27 passed**

## Next

Remaining contract work: [PC00_certificate_contract.plan.md](PC00_certificate_contract.plan.md)  
Patchset: [PRODUCTION_CERTIFICATION.plan.md](PRODUCTION_CERTIFICATION.plan.md)
