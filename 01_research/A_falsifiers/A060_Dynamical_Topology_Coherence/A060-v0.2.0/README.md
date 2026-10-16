# A060 v0.2.0 - DEVELOPMENT reference preflight for M00--M04

This is a **tested, self-contained development overlay** for A060 Cross-Paper Vortex Mechanics & Stability. It is **NOT** an instance produced by the official v1.0.7 generator and it has not gone through canonical FREEZE / CERTIFY / REVEAL. It must not overwrite A060 v0.1.0 or the frozen framework.

## Verified local work

`pytest -q` -> six passing tests. `python -m a060_preflight --source-dir <path-to-the-four-supplied-papers>` -> development ledger `preflight_outputs/PRECHECK_RESULTS.json`. M00 only passes source SHA-256 if the original source PDF bytes match; absent source is UNRESOLVED, not a PASS. M00's registry reconciliation is explicitly unresolved even when PDF hashes all match.

Run in Windows:

```cmd
py -3 -m pip install -r requirements.txt
run_preflight.cmd SELFTEST
run_preflight.cmd PRECHECK "C:\path\to\PDFs"
```

The working module has **no canonical SST constants in blind scoring**. All mechanics are dimensionless reference controls.

Read `docs/IMPLEMENTATION_PLAN.md` and the preflight design PDF first. The plan details official v1.0.7 generator integration, G0--G9 mapping, all numerical gates, and PDF/ZIP report contract.

**Critical Google Drive findings:** existing A060 v0.1.0 has framework v1.0.6, and the accessible Sep-25 registry calls A045 a different family from recent A045 triadic geometry material. This mismatch blocks formal M00 registry certification pending reconciliation.
