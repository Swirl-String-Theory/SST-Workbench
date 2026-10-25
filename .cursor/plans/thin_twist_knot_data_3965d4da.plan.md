---
name: Thin twist knot data
overview: Dun de A006 twist-catalogus uit tot links alleen FLAT/SOFT op N=512/1024, met harde limiet file size onder 50 MB; werk UI-defaults, asserts, docs en hashes bij.
todos:
  - id: add-prune-filter
    content: catalog_entry_allowed + --prune-catalog in build_twist_knot_data.py (+ unit tests)
    status: pending
  - id: prune-both-copies
    content: Prune beide twist_knot_data.js-kopieën naar 139 entries en verifieer size < 50 MB
    status: pending
  - id: update-ui-runtime
    content: index.html profile-opties/default FLAT; runtime fallback + assert 139
    status: pending
  - id: docs-hashes-tests
    content: README counts, source-hashes.json, her-run unit tests
    status: pending
isProject: false
---

# Thin twist_knot_data.js (links 512/1024, drop BALANCED/TIGHT, <50 MB)

## Scope

Huidige catalogus ([`apps/web/data/twist_knot_data.js`](05_apps/A003_vortexlab/apps/web/data/twist_knot_data.js)): **235** IDs (128 links + 107 knots/seeds/qual), **~87.7 MB**.

**Harde eis:** gegenereerde `twist_knot_data.js` **onder 50 MB** (pretty-print, zoals nu).

Na uitdunnen:

- **Links behouden:** alleen `FLAT` en `SOFT`, alleen `N=512` en `N=1024` → **32** links (~12 MB)
- **Links weg:** alle `BALANCED`/`TIGHT`, plus FLAT/SOFT op N=256/2048 → **96** drop (~48 MB)
- **Knots/seeds/qual:** ongewijzigd (inclusief N256/N2048, ~17 MB)
- **Nieuw totaal: 139** entries
- **Verwachte size: ~30 MB** (ruim onder 50 MB; gemeten via DB-payload-schatting)

UI-default voor profile wordt **FLAT** (BALANCED verdwijnt).

Geen verdere knot-uitdunning of `--compact` nodig voor de 50 MB-grens; pretty-print blijft.

## Aanpak (geen Fourier-herbouw)

Het bestand is gegenereerd; handmatig knippen is riskant. Gebruik de bestaande load/write-paden in [`build_twist_knot_data.py`](05_apps/A003_vortexlab/tools/catalog/build_twist_knot_data.py) (`read_existing_database` / `write_javascript`):

1. Voeg catalogus-includefilter toe, bv. `catalog_entry_allowed(entry)`:
   - non-`LINK` → altijd behouden
   - `LINK` met `profile in {BALANCED, TIGHT}` → drop
   - `LINK` met `resolutionN not in {512, 1024}` → drop (qual met `profile=null` blijft)
2. CLI-flag `--prune-catalog` die bestaande JS inleest, filtert, herschrijft (pretty-print)
3. Optioneel dezelfde filter bij `--fresh`/`ingest` zodat toekomstige regeneraties dun blijven (`--link-profiles FLAT,SOFT` + `--link-resolutions 512,1024`)

Uitvoeren op beide canonieke kopieën:

- [`apps/web/data/twist_knot_data.js`](05_apps/A003_vortexlab/apps/web/data/twist_knot_data.js)
- [`vortexring-lab/twist_knot_data.js`](05_apps/A003_vortexlab/vortexring-lab/twist_knot_data.js)

## UI + runtime

In [`apps/web/index.html`](05_apps/A003_vortexlab/apps/web/index.html):

- Verwijder `<option>` BALANCED en TIGHT uit `#twistProfileFilter`
- Zet `selected` op **FLAT**

In [`apps/web/src/legacy/vortexlab-runtime.js`](05_apps/A003_vortexlab/apps/web/src/legacy/vortexlab-runtime.js):

- Fallback `twistProfileFilter` default: `'BALANCED'` → `'FLAT'`
- Console assert `tw.ids.length===259` → `===139` (huidige file heeft al 235; assert is stale)
- Filter-assert die `profile:'BALANCED'` gebruikt mag `'FLAT'` worden (knots negeren profile sowieso)

N-filteropties 256/2048 blijven (nodig voor knots).

## Docs / provenance

- [`docs/TWIST_KNOTS_DATA_README.md`](05_apps/A003_vortexlab/docs/TWIST_KNOTS_DATA_README.md): counts 139, link-subsetregel, UI-default FLAT, rebuild-instructie met prune/filters
- [`reference/source-hashes.json`](05_apps/A003_vortexlab/reference/source-hashes.json): hash van `twist_knot_data.js` herberekenen

## Tests

Uitbreiden in [`tools/catalog/tests/test_build_twist_knot_data.py`](05_apps/A003_vortexlab/tools/catalog/tests/test_build_twist_knot_data.py):

- unit tests voor `catalog_entry_allowed` (link N/profile, knot passthrough, qual passthrough)
- parse-tests voor BALANCED-stems blijven (stem-parsing blijft geldig; alleen catalogusinhoud dun)

Vooraf: 19 tests OK. Na afloop opnieuw `python -m unittest tests.test_build_twist_knot_data -v`.

## Validatie na prune

- `TWIST_KNOT_IDS.length === 139`
- geen ID met `_BALANCED_` of `_TIGHT_`
- geen `LINK_*_N0256_*` of `LINK_*_N2048_*`
- wel `LINK_*_FLAT|SOFT_N0512|N1024_*`
- **file size `< 50_000_000` bytes** op beide canonieke paden (fail als ≥50 MB)