# Repair classification — evidence-first

**Verified from uploaded/retrieved records:** v0.3.0 coordinator records FREEZE exit 1, BASIC exit 2, 2048 exit 2, FULL exit 1; additional INSTALL result was not evaluated here. Prior v0.3.0 coordinator did not capture native runner stdout in `COORDINATOR_EXECUTION.json`; no root cause can be deduced from those codes alone. v0.2.9 BASIC has G1/G2/G8 FAIL in a different evidence lineage; v0.2.10 prior selected-32768 outcome has gates PASS at finite horizons but is not automatically comparable or a repair of the v0.3.0 clone.

**Confirmed structural bug and fix:** the original `.sst_framework_root` locator uses `../../../../06_templates/...v1.0.8`. In the v0.3.0 clone the same relative expression resolves four levels above the cloned directory rather than four levels above the original v0.2.9 directory; this breaks deterministic pinned-framework loading in `framework_bootstrap.py` whenever no explicit environment override was present. The v0.3.1 coordinator now resolves the root relative to the source root recorded in the SHA-verified clone manifest and injects `SST_FALSIFIER_FRAMEWORK_ROOT` (pinned v1.0.8) when launching the original engine; it leaves all cloned frozen source files unchanged. This is a reproducible structural defect; it is not proof that every reported native exitcode was caused exclusively by it.

**Changed:** coordinator per-run native stdout capture + non-overwriting execution records; legacy workspace attach; explicit DIAGNOSE and AUDIT_CONTROLS; opt-in new KnotPlot command probe scripts. No source engine or scientific gate semantics changed.

**Not changed:** old 271-condition matrix, eight anonymous axes, all source and private fingerprints, runtime geometry, freeze commitment, conclusions.

**Unresolved:** actual failure mechanism inside legacy Windows source, `No Collide` GUI-to-CLI mapping, `tinc` versus `timeincr`, tangential-force implementation bug, Native KnotPlot acceptance of the new commands, any new physically significant dynamic claims.
