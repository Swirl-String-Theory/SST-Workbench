# CHANGELOG

## v0.3.0 — pinned KnotRecord integration

- Require exact SST Knot Library v0.2.5 for the designated prospective scientific atlas.
- Verify dependency `RELEASE.json`, full manifest, KAtlas snapshot and source-catalog hashes.
- Freeze the knot-library dependency attestation in preregistration and run evidence.
- Load Fremlin/Gilbert parents through SST Knot Library and construct the braid parent from
  its pinned KAtlas reference.
- Re-load every generated test realization through `make_knot_record(expected_topology="3_1")`.
- Commit a portable KnotRecord SHA-256 per test source and re-verify it before scoring.
- Preserve the independent N=64/96/128 numerical trefoil diagram witness; do not elevate
  KAtlas reference-only status to external geometry certification.
- Add publication topology gate requiring an external provider or interval/ambient-isotopy proof.
- Fix package-version provenance: Python runtime, pyproject, native setup, batch banners and
  RELEASE.json now all report 0.3.0.
- Add `run_all_atlas.cmd` one-click frozen atlas + screen + Phase-B + reveal workflow.
- Preserve v0.2.2 S37 threshold and all numerical/physics gates unchanged.
