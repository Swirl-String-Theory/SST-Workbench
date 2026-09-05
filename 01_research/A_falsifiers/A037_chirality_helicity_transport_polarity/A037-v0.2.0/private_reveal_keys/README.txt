Reveal keys created by run_10_prepare.cmd are stored here as random <key_id>.json files.
They are intentionally OUTSIDE outputs\... and therefore are not included by run_35_archive_blind.cmd.
Do not delete the matching key before running run_40_reveal.cmd.
After reveal, a verified REVEAL_MAPPING.json is copied into the output directory so the *_REVEALED.zip is self-contained.
