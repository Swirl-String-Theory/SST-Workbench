# Repository-wide source auto-discovery — builder v0.2.0

The builder no longer assumes that SST knot sources remain at one historical path. It loads the authoritative `A001`–`A008` source-location catalogue and searches in three passes:

1. **legacy exact paths** from the catalogue;
2. **post-restructure destinations** under `03_data/A_knots/...`;
3. **repo-wide alias search** when an authoritative path is absent.

The scan is provenance-only. Discovery does not imply geometry admission.

## A001–A008

| ID | Source family | Important treatment |
|---|---|---|
| A001 | KnotPlot relaxed | scans all relaxation stages, not only `final`; stage is retained as metadata |
| A002 | KnotPlot Fourier-series | remains a separate source family until byte hashes prove a Fremlin mirror |
| A003 | KnotPlot QHP | explicit source family; unsupported representations fail closed |
| A004 | Gilbert ideal | multi-record `Ideal*.txt.gz`; selection/triage files are provenance anchors |
| A005 | KAtlas source crawl | topology/reference source; 3-D artifacts remain derived controls |
| A006 | Fremlin Fourier-series | source-native `.fseries` / qualified `.short` paths |
| A007 | Knot Library source graph | `Sources`, `Derived`, `Registry`, and `Quarantine` are different roles |
| A008 | PTSA v1.0.0 | source-native candidate XYZ files preferred over PKLSA-v0.2.0 fallback copies |

## Fast scan versus deep hash

`run_repo_scan.cmd` inventories every file but avoids hashing every multi-GB source byte. It always hashes selected reference/provenance anchors and later hashes every geometry file actually admitted as a carrier.

`run_repo_scan_deep.cmd` additionally SHA-256 hashes every discovered source file. This can be expensive on A001 (~multi-GB).

The fast directory fingerprint is deterministic over `(relative path, size, mtime_ns)` and is explicitly labelled as a fingerprint rather than a content hash.

## Unregistered source candidates

The repo walk also looks for high-confidence source-like directories outside the current A001–A008 roots, including KnotInfo, LinkInfo, Ridgerunner, KAtlas, Fremlin, KnotPlot, PTSA, and QHP material. These are written to:

`source_discovery/UNREGISTERED_SOURCE_CANDIDATES.json`

They are not silently admitted. Publication mode may use `--fail-on-unregistered` to force manual classification first.

## Mirror handling

Exact byte identity is sufficient to collapse evidence independence. For example, if an A002 `.fseries` file is byte-identical to the A006 Fremlin source, the A002 record remains in provenance but inherits the Fremlin independence group and is marked as a mirror.

A mere equality of reconstructed geometry hashes is *reported* but does not automatically collapse independently obtained sources.
