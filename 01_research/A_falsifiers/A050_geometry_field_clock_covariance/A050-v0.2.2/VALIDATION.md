# VALIDATION — v0.2.2

Build qualification requires:

- seal verification passes;
- all unit tests pass;
- blind audit reports zero forbidden identifiers/fingerprints in `sst_gfcc_blind`, `config`, and `data`;
- all 20 holdout files match the SHA-256 hashes in `data/HOLDOUT_MANIFEST.json`;
- v0.2.0 legacy threshold blocks match byte-for-value with the v0.2.2 default configuration;
- Floquet policy is inactive.

Scientific qualification additionally requires execution of the full default campaign. Merely passing unit tests or a smoke run is not a scientific v0.2.2 result.
