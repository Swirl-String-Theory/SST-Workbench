# Paper-upgrade certificate gaps (PU02 → PU02b)

Campaign solvers do **not** yet write the gate inputs (\(g,H,C\) for A034; \(\chi_{ij}\) /
orientation sweeps for A037; mode grid for A030) into stable JSON under `outputs/`.

Until `from_outputs` extractors land per family:

- `paper_upgrade_certs.py emit-*-synthetic` is used to prove the certificate **pipeline**
  (emit → path → consumer) after campaigns.
- Those emits MUST be marked `certificate_kind=SELFTEST`, `scientific=false`,
  `promotion_allowed=false`, `status=PIPELINE_PASS` ([PU02b](PU02b_certificate_semantics.plan.md)).
- Scientific PASS/FAIL of the new observables still requires extracting real tensors from
  campaign artifacts (PU04b–PU04d).

Canonical certificate path: `outputs/<tier>/paper_upgrade/certificate.json`

Env overrides: `SST_A034_CERT`, `SST_A037_CERT`, `SST_A030_CERT`

Consumer rule: authorize downstream **only** if `promotion_allowed` is true.
