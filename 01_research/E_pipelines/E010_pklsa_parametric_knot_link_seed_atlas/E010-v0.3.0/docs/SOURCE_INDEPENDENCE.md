# Source-independence ledger

The ledger separates four evidence classes:

- `UPSTREAM_REFERENCE`: independently sourced geometry/reference artifact;
- `DERIVED_CROSS_METHOD`: a materially different numerical construction retaining parent lineage, e.g. Ridgerunner from a KnotPlot seed;
- `MIRROR_NOT_INDEPENDENT`: byte/source mirror of another upstream family;
- `GENERATED_FAMILY`: PTSA/SIAF/parameter controls.

It reports raw-byte duplicates and post-load geometry duplicates separately. A shared `independence_group` prevents variants from being counted as independent observations.

Two useful counts are emitted:

`strict_upstream_independent_group_count` counts only upstream reference groups.

`upstream_plus_cross_method_group_count` also counts derived cross-method groups, while still retaining their parent lineage.

This makes a statement such as “four independent carriers agree” auditable instead of equating four files with four independent data sources.
