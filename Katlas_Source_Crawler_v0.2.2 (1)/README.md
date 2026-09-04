# SST Katlas Source Crawler v0.2.2

Builds a reproducible offline Knot Atlas source catalog in:

```text
Katlas_Sources_v0.2.2_Outputs/
```

## Full one-click run

```bat
run_all.cmd
```

The full chain is:

```text
official Katlas RDF download
        ↓
export all knots through 12 crossings present in the RDF
        ↓
export all links present in Links.rdf.gz
        ↓
create SQLite / JSONL / CSV catalogs + friendly aliases
        ↓
fetch curated Katlas raw wikitext + rendered HTML
        ↓
extract ArcPresentation + semantic notes + diagram/image refs
        ↓
merge enrichment into katlas.json
        ↓
strict source-to-export validation
```

For a bulk/offline RDF-only build:

```bat
run_all_rdf_only.cmd
```

## Verified official-source counts

Using the supplied official v0.2.1 source archives as the input fixture, v0.2.2 exports:

```text
Rolfsen knots       250
11-crossing knots   552
12-crossing knots  2176
Links              1424
-----------------------
Canonical total    4402
```

The link split is:

```text
2 crossings       1
4 crossings       1
5 crossings       1
6 crossings       6
7 crossings       9
8 crossings      29
9 crossings      83
10 crossings    287
11 crossings   1007
```

The official `Links.rdf.gz` used here contains no 12-crossing link objects; v0.2.2 does not fabricate them.

## Important Links.rdf.gz compatibility rule

Katlas currently encodes link records such as:

```text
<knot:L2a1> <invariant:PD_Presentation> "..." .
```

So the RDF namespace says `knot:` even though `L2a1` is a link. v0.2.2 deliberately treats the identifier syntax as authoritative:

```text
L6a4  -> link
L10n113 -> link
K11a367 -> knot
9_2 -> knot
```

This fixes the v0.2.1 condition where every link was classified as an unrecognized ID.

## Output layout

```text
Katlas_Sources_v0.2.2_Outputs/
  _source/
    Rolfsen.rdf.gz
    Knots11.rdf.gz
    Knots12.rdf.gz
    Links.rdf.gz
    SOURCE_MANIFEST.json

  _catalog/
    catalog.sqlite3
    catalog.jsonl
    catalog.csv
    aliases.json
    BUILD_REPORT.json
    VALIDATION_REPORT.json
    CATALOG_SUMMARY.json
    PAGE_FETCH_sst_curated_REPORT.json

  knots/
    03/3_1/
    ...
    10/rolfsen/....
    10/10_1/                 # friendly duplicate
    11/alternating/....
    11/nonalternating/....
    11/11_1/                 # duplicate -> K11a367
    11/11_2/                 # duplicate -> K11a247
    12/alternating/....
    12/nonalternating/....

  links/
    02/L2a1/
    04/L4a1/
    ...
    09/L9.../
    10/alternating/....
    10/nonalternating/....
    11/alternating/....
    11/nonalternating/....
```

Crossings below 10 remain shallow. Canonical objects from crossing 10 upward are sharded in groups of 50.

## Per-object RDF data

Every canonical object has:

```text
katlas.json
source.rdf.nt
```

`katlas.json` retains the exact source identity, available presentations and every RDF invariant. Depending on Katlas coverage this can include PD, Gauss, DT, Conway, braid and many polynomial/topological invariants.

## Three web-only enrichment layers

The full `run_all.cmd` additionally fetches the curated profile (all knots and links through 7 crossings plus the configured higher favorites). Each fetched object receives:

```text
page.wikitext
page.html
page_enrichment.json
```

### 1. ArcPresentation

When present on the rendered/raw Katlas page it is stored in:

```json
{
  "presentations": {
    "arc": ["..."]
  }
}
```

and repeated with provenance in `page_enrichment.json`.

### 2. Semantic / human notes

Quick Notes, Further Notes / Views and notes-on-presentations text is preserved under:

```text
page_enrichment.semantic_notes
```

This is enrichment only; it never overrides canonical RDF invariants.

### 3. Diagram / image references

MediaWiki `File:` / `Image:` references plus rendered page image/media references are stored under:

```text
page_enrichment.media_references
```

The crawler stores references and page snapshots, not a blind mirror of every image binary.

## Friendly Fremlin aliases

The direct convenience duplicates are deliberate and documented:

```text
10_1    -> canonical Rolfsen 10_1
10_2    -> canonical Rolfsen 10_2
10_124  -> canonical Rolfsen 10_124
11_1    -> K11a367
11_2    -> K11a247
```

`11_1` and `11_2` exist because those names match the favorite/Fremlin convention and are much easier to remember than the Hoste-Thistlethwaite IDs. `ALIAS.json` always records the canonical target; `katlas.json` keeps the canonical Katlas identity.

## Curated page profile

Automatically fetched in `run_all.cmd`:

- every knot and link through 7 crossings;
- `8_1`, `8_3`, `8_9`, `8_12`, `8_17`, `8_19`;
- `9_1`, `9_2`;
- `10_1`, `10_2`, `10_124`;
- `K11a367` (`11_1`);
- `K11a247` (`11_2`);
- `L8a1`.

Existing page snapshots are skipped by default, so the operation is resumable. Use `run_fetch_curated.cmd --force` to refresh them.

## Strict validation

`run_validate.cmd` reparses every local official RDF archive and compares the number of parseable source objects with the number actually exported. Therefore a recurrence of the v0.2.1 link bug becomes a hard `FAIL`, not a silent pass.

When a curated page-fetch report exists, validation also requires `page.wikitext`, `page.html`, `page_enrichment.json`, and merged `page_enrichment` in `katlas.json` for every selected object.

## Tests

```bat
run_tests.cmd
```

Covers naming/sharding, RDF parsing, the official link namespace quirk, aliases, curated selection, page snapshot synchronization, and all three enrichment layers.
