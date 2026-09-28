# Blind protocol

Create a new uniquely named run; freeze the configuration, source-manifest hashes and a commitment to the complete private label key before analysis. No canonical SST values or keys may enter BLIND, including equivalent numeric encodings. Scan the final JSON/CSV/text/NPZ inventory before sealing; do not echo forbidden values in diagnostics.

Seal the complete file inventory. An external run-local seal commitment binds its bytes and the run identity. Verify additions, deletions, modifications, configuration, label key and source-manifest commitment before importing reveal-only constants. The source tree is checked at sealing; historical verification uses the recorded source hashes, so subsequent documentation edits do not invalidate old runs. Keep the external commitment/hash separately if adversarial protection is required: this is tamper evidence, not an external digital signature or trusted timestamp.

Revealed reports have a closed inventory too. Repeating reveal verifies it and is idempotent; partial or modified reports are rejected. Packaging creates new ZIPs exclusively, with SHA-256 sidecars. PRIVATE is excluded from distributions; the verified key is present in REVEALED only. Full output packages contain both scopes and are not blind-only artifacts.

The analysis code knows the candidate functional forms. Blinding covers labels and SST constants; it does not make the researcher unaware of the hypothesis or knot family.
