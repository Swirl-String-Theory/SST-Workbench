# Idempotency fix

This patch supersedes the previous 8_5 restore/final-repair drop-in only in repair-runner control flow.
It does **not** change geometry qualification mathematics or the 8_5 source bytes.

If `FAILED_TOPOLOGIES.json` is already empty, the runner now:

1. requires `CAMPAIGN_INDEX.json` to report `passed_count == topology_count` and `failed_count == 0`;
2. requires every topology's `PRODUCTION_GATE.json`, `summary.json`, and identity gate to be green;
3. requires `RELEASE.json` to be publication-green with zero failed topologies;
4. performs a fresh deep SHA-256 scan and requires the registered A001-A008 source inventory to match the completed run;
5. writes `REPAIR_ALREADY_COMPLETE.json`, packages the atlas, and exits 0.

Any inconsistency still fails closed.
