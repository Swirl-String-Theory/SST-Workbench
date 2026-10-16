# v1.0.8 local validation — 2026-10-13

- Source: reconstructed from the **92-file** v1.0.7 Drive package manifest; all previous paths accounted for. New source edits confined to output/run policy, report publishing, blind archive exclusions, version metadata and tests.
- `PYTHONPATH=. pytest -q`: **64 PASS**, no failures at initial release build.
- End-to-end generated-instance exercise: `FREEZE`, `BASIC` twice, two BLIND ZIPs, two independently compiled PDF reports, and preserved archive with prior output manifest — **PASS**.
- Same ID holds BLIND vs REVEALED; publication files refuse replacement. Lock concurrent-entry rejection — **PASS**.
- No registered scientific gates, core mathematical kernels, numerical threshold settings, C++ implementation or SYCL kernel altered.
- v1.0.8 was tested on the model's Linux environment, **not** the user's Windows/Intel Arc A770 target machine. CPU/SYCL backend validation on that machine remains required for production freeze.
- `PARENT_CANONICAL_FREEZE.json` retains the original v1.0.7 canonical release declaration.
