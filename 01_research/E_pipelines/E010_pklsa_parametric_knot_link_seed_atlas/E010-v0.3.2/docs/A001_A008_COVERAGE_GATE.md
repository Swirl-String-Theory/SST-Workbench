# A001–A008 hard source-coverage gate

Before high-resolution geometry qualification begins, the builder produces a source-coverage audit.

Allowed terminal source states are:

- `INGESTED`
- `INGESTED_METADATA_ONLY` (used only where the catalogued container genuinely provides registry/provenance rather than a centerline)
- `SOURCE_UNAVAILABLE_WITH_PROVENANCE`

Blocking states include:

- `EXPECTED_SOURCE_MISSING`
- `DECLARED_SUBSOURCE_MISSING`
- `EMPTY_SOURCE_ROOT`
- `FORMAT_UNSUPPORTED_OR_METADATA_ONLY`

For sources with multiple declared subpaths, each path is checked independently. This is especially important for A007, where `Sources/`, `Derived/`, `Registry/`, and `Quarantine/` are all explicit parts of the source graph.

A source marked absent in the authoritative catalogue (for example a historical legacy path already known to be missing) may terminate as `SOURCE_UNAVAILABLE_WITH_PROVENANCE`. This is not interpreted as a scientific success; it is an auditable absence rather than silent omission.

Output files:

- `source_discovery/A001_A008_COVERAGE.csv`
- `source_discovery/REPO_SOURCE_DISCOVERY_SUMMARY.json`
- `source_discovery/REPO_SOURCE_DISCOVERY.json.gz`
- `source_discovery/UNREGISTERED_SOURCE_CANDIDATES.json`

The normal `build` command is strict by default. `--allow-source-gaps` exists only for diagnostic migration work.
