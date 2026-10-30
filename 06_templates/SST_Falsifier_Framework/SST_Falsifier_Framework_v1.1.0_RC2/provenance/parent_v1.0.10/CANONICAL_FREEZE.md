# SST Falsifier Framework v1.0.10 — CANONICAL_FROZEN

**Freeze date:** 2026-10-19. **Source parent:** v1.0.9 CANONICAL_FROZEN. **Functional source:** v1.0.10 RC2.

## Release integrity

- Canonical source built exclusively from `SST_Falsifier_Framework_v1.0.10-RC2-CLEAN_CANDIDATE.zip`.
- RC2 source ZIP SHA-256: `b19e2d71c94aa3ad4c28e52b2c7276a69ee42c965493bd1ec5c04378029b91d1`.
- Original RC2 package manifest verified for all 110 tracked files.
- Only release documentation/status, manifest, freeze records and packaging metadata have changed; scientific/runtime/backend source is byte-for-byte identical to RC2.

## Windows evidence

- Framework regression: 83/83 PASS; wheel installed as 1.0.10.
- `run_all.cmd ALL`: native C++/OpenMP FP64, Intel Arc A770 SYCL FP32/DD32 and DD32 directional stress PASS.
- `run_all.cmd DD32`: PASS; C++ deliberately SKIPPED.
- Non-short-circuit smoke: G2 FAIL; G3 and G8 executed and returned PASS with DIAGNOSTIC_ONLY, reveal ineligible.
- Two-run identity smoke: two PDFs, two BLIND ZIPs, old output archived.
- User Windows log SHA-256: `4f3eb9690aff159cf3ed09416ce501ae82dba51839784bc99bd591a1448f82b3`.

**Provenance limit:** user copied RC2 over RC1 in an existing folder; Windows execution is evidence of that overlay installation, not independent clean-extraction validation. The canonical *source artifact* is created only from the separately checked RC2 ZIP. The frozen source is intentionally independent from caches, wheels, and native build artifacts in that Windows folder.

**Scientific limits:** Parity tests certify the tested Biot--Savart backend kernels, not full Euler/PKLSA dynamics or SST physical claims. SYCL DD32 stays SCREENING_ONLY. Historical falsifiers keep their existing pinned framework unless explicitly migrated.
