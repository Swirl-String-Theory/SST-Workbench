# Changelog

## v0.2.2

- Replaces the non-existent E010-v0.4.0 source dependency with the real E011/SKLSA-v0.3.0 `STATIC_READY` falsifier-facing atlas derived from E010/PKLSA-v0.3.1.
- Accepts E010-v0.3.1 as parent qualification even though its global `full_campaign_gate_pass` and `publication_ready_geometry_layer` are false; requires E011 `execution_gate=PASS`, zero operational errors, and the E010 source/topology/identity admission gates.
- BASIC/FULL use deterministic E011 provider anchors; CERTIFY uses all E011 primary upstream `STATIC_READY` carriers.
- Adds source-native `xyz`, strict Geomview `vect`, and `gilbert_ab_record` loading with exact raw-source SHA-256 validation.
- Adds Windows-path-to-current-Workbench suffix recovery for E011 source locators.
- Preserves X0 provider-collapse semantics; CERTIFY same-provider disagreements become `INTERNAL_INCONSISTENCY`.
- Adds an E011 preflight to `run_all.cmd` so missing/invalid dependencies fail before expensive science execution.
- No H0–H4/P0–P6/X0 threshold was retuned.

## v0.2.1

- Introduced PKLSA provider-level X0 cross-source consistency but targeted an E010-v0.4.0 release not present in the real Workbench.
