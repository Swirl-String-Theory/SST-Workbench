# CHANGELOG

## v0.1.1

- Renamed campaign identity from erroneous E011 to canonical E013.
- Replaced direct E010 geometry-metrics scraping with E011 SKLSA STATIC_READY provider-anchor consumption.
- Added E011 release/schema/execution-gate validation.
- Changed carrier policy to 1 anchor in BASIC, up to 2 provider anchors in FULL/CERTIFY.
- Optional non-STATIC_READY topologies no longer abort the campaign.
- Required core is restricted to 3_1, 5_2, 6_1 and 4_1.
- PLAN/BASIC can complete as READY_NO_MEMBERS before downstream A-falsifier successors are registered.
- Updated environment and member-contract schema to explicitly require E013/E011 SKLSA common carriers.
