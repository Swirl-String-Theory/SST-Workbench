# Validation — A054 v0.1.1 build snapshot

Validation performed in the ChatGPT execution container on 2026-10-06.

- Python tests: **12 passed**.
- Native-equivalence test: **1 skipped** because `pybind11` is not installed in this offline container.
- Full-factorial bookkeeping with a mocked one-pair provider stratum: PASS (`3 + 3*8 = 27` anonymous candidates).
- Partial preparation without Workbench: PASS; exactly 3 anonymous analytic controls and `scientific_ready=false`.
- Isolated blind-runner semantic leak scan: PASS.
- Blind runner executes after the private map is removed from reach: PASS.
- BLIND/REVEALED archive packer excludes `_private` and writes archive-content SHA-256 manifests: PASS.
- Mock full-factorial prepare/blind/reveal integration smoke: PASS (27 cells for one provider stratum; 24 skeleton contrasts, 36 single-site twist contrasts, 12 polarity-by-knot grouped summaries).
- Backend qualification ledger and blind seal: PASS.
- BASIC analytic-control smoke campaign: PASS using NumPy reference backend; reveal seal verification PASS.
- Constant-final-time `dt(N) ~ N^-2` unit test: PASS.
- Prospective polarity-gate unit test: PASS.
- SO(3) objectivity including separation-curvature diagnostic: PASS.
- v0.1.0 discovery provenance frozen with source archive SHA-256 `c4fddcdd29cce9cd7ccd38412725d5c43dc584b330c1bfd12ec3586ae614cd93`.

No production v0.1.1 PKLSA campaign was executed in this container because the local SST-Workbench source archives are not mounted. The package therefore makes no v0.1.1 scientific verdict here.
