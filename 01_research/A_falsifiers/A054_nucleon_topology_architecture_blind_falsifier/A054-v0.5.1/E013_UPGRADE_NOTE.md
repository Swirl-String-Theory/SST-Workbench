# E013 v0.1.1 duplicate-member note

E013-v0.1.1 discovers every enabled `cross_falsifier_contract.json` recursively and does not deduplicate multiple versions of the same catalog ID. If A054-v0.5.0 remains in the Workbench with its contract enabled, E013-v0.1.1 will discover both v0.5.0 and v0.5.1 and run both at stage 30.

For a clean v0.5.1 campaign, preserve the frozen v0.5.0 package/output archives but make its member contract non-discoverable before the new E013 run (for example rename only the old `cross_falsifier_contract.json` to `cross_falsifier_contract.v0.5.0.frozen.json`). Do not alter the v0.5.0 scientific outputs.

After that, `run_all_cross_falsifier.cmd PLAN ...` should list A054-v0.5.1 and A057-v0.2.0 as the active members.
