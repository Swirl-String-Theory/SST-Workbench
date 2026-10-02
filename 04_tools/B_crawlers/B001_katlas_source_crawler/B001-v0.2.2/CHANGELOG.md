# Changelog

## v0.2.2

- Fixed official `Links.rdf.gz` import. Katlas currently stores `L...` link IDs under the RDF subject namespace `knot:`; v0.2.2 therefore treats identifier syntax as authoritative and exports every parseable `L<crossings><a|n><ordinal>` as `kind=link`.
- Strict source-to-export validation: every downloaded RDF dataset is reparsed during validation and its parseable object count must exactly equal the exported SQLite/filesystem count.
- Full tested export from the supplied official archives: 2,978 knots + 1,424 links = 4,402 canonical objects; zero skipped identifiers.
- `run_all.cmd` now performs the full chain and writes to `Katlas_Sources_v0.2.2_Outputs`.
- Added curated page enrichment in the same run:
  - ArcPresentation extraction;
  - semantic/human note extraction;
  - diagram/image/media reference extraction.
- Curated page fetch stores both `page.wikitext` and rendered `page.html` for reproducibility.
- Adds `page_enrichment.json` per fetched object and mirrors the extracted data into `katlas.json`; ArcPresentation is also exposed under `presentations.arc`.
- Friendly duplicates (`10_1`, `10_2`, `10_124`, `11_1`, `11_2`) synchronize page snapshots and enrichment metadata.
- Added `_catalog/CATALOG_SUMMARY.json` with object counts and presentation coverage.
- Added enrichment regression tests and the link namespace regression test.

## v0.2.1

- Added Fremlin/SST-friendly duplicates and `11_1 -> K11a367`, `11_2 -> K11a247` aliases.
