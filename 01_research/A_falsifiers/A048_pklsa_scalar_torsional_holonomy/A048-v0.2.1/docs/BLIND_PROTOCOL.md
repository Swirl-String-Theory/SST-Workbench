# Blind protocol

Create a new uniquely named run; freeze the configuration, source-manifest hashes and a commitment to the complete private label key before analysis. No canonical SST values or keys may enter BLIND, including equivalent numeric encodings. Scan the final JSON/CSV/text/NPZ inventory before sealing; do not echo forbidden values in diagnostics.

Seal the complete file inventory. An external run-local seal commitment binds its bytes and the run identity. Verify additions, deletions, modifications, configuration, label key and source-manifest commitment before importing reveal-only constants. The source tree is checked at sealing; historical verification uses the recorded source hashes, so subsequent documentation edits do not invalidate old runs. Keep the external commitment/hash separately if adversarial protection is required: this is tamper evidence, not an external digital signature or trusted timestamp.

Revealed reports have a closed inventory too. Repeating reveal verifies it and is idempotent; partial or modified reports are rejected. Packaging creates new ZIPs exclusively, with SHA-256 sidecars. PRIVATE is excluded from distributions; the verified key is present in REVEALED only. Full output packages contain both scopes and are not blind-only artifacts.

The analysis code knows the candidate functional forms. Blinding covers labels and SST constants; it does not make the researcher unaware of the hypothesis or knot family.


## v0.2.0 executed cycle

A048_PKLSA_Scalar_Torsional_Holonomy_Falsifier_v0.2.0_authenticated-trefoil-euler-smoke_20260925T135804911694Z_856cf4bc

Independent Euler producer smoke completed with physical verdict INDETERMINATE; see CYCLE_EVALUATION.md. All time series and full initial/final fields were sealed before reveal. Core-phase and evolved-centerline observables are absent, not zero. No SST canonical value enters the independent producer.


## v0.2.1 final cycle

47 tests passed, including portable package verification. BLIND and REVEALED remain separate; the complete outputs package includes both. The final physical verdict is INDETERMINATE_UNQUALIFIED_CORE_AND_MISSING_MATERIAL_OBSERVABLE. No canonical constants enter the producer. Recorded run: A048_PKLSA_Scalar_Torsional_Holonomy_Falsifier_v0.2.1_portable-euler-regression_20260925T140154511767Z_36ad581b. See CYCLE_EVALUATION.md.
