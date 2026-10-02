---
name: PC05 provenance ledger
todos:
  - id: t00
    content: "Define stage ledger JSON schema (inputs, config, commit, backend, gates, output hash)"
    status: pending
  - id: t01
    content: "Wire ledger write into paper_upgrade_runtime stage wrapper"
    status: pending
  - id: t02
    content: "Downstream certs embed upstream cert hashes (provenance DAG)"
    status: pending
---
# PC05 — Provenance ledger (optional, repo-wide)

Status: `PLANNED` · Priority: P2 · Risk: low  
Depends on: [PC00](PC00_certificate_contract.plan.md)  
Epic: [PRODUCTION_CERTIFICATION.plan.md](PRODUCTION_CERTIFICATION.plan.md)

Every scientific stage writes:

```json
{
  "producer": "A037-v0.3.1",
  "input_files": [{"path": "...", "sha256": "..."}],
  "config_sha256": "...",
  "code_commit": "...",
  "backend": "...",
  "numerical_gates": {},
  "output_sha256": "..."
}
```

Downstream certificates include upstream cert hashes:

\[
H_{\mathrm{A038}}
\supset
H_{\mathrm{cert}}^{A034},\;
H_{\mathrm{cert}}^{A037}
\]

yielding a provenance DAG useful for blind/reveal research.

Do **not** block PC01–PC04 on this; land after firewall + first promotable certs.
