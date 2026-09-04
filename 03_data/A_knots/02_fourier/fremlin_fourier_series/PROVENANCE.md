# Data provenance — Ideal_Fremlin_Fseries

**Status:** companion archive to Ideal_Sources, same hashing policy.
**Scope:** David Fremlin’s public knot realizations at
https://david.fremlin.de/knots/.

---

## 1. Directory layout

```
SST-Workbench/Ideal_Fremlin_Fseries/
  SOURCE.md                 # URL, retrieval date, licence note
  PROVENANCE.md             # this file
  MANIFEST.json             # sst-provenance/1 hashes over fremlin/
  sst_provenance.py         # same tool as Ideal_Sources
  download_fremlin_knots.py # re-fetch crawler
  tests/                    # offline unit tests
  fremlin/                  # immutable. Never edited, never normalised.
    3_1/
    …
    15331/
```

Rules (same spirit as Ideal_Sources/PROVENANCE.md):

- **`fremlin/` is read-only** after download. Exact upstream bytes; no
  line-ending conversion, no reformatting, no merging with ideal.txt.
- **Consumers read from `fremlin/` or from a derived artifact with a recipe.**
- Homemade / Gilbert-ideal conversions do **not** belong here (those were
  previously contaminating `Knots_FourierSeries` as `9_2` and `10_1`).

---

## 2. Three hash levels

`MANIFEST.json` is produced by `sst_provenance.py` with schema
`sst-provenance/1`. For Fremlin assets (plain files, not `.gz`), container and
payload hashes coincide. Canonical hashes still survive CRLF drift on text
`.fseries` / `.short` / `.scad` files.

| Field | Use |
|---|---|
| `sha256_container` | exact file on disk |
| `sha256_payload` | citable identity |
| `sha256_canonical` | content compare ignoring EOL |

Verify:

```
python sst_provenance.py verify fremlin -m MANIFEST.json
```

---

## 3. Attribution

Cite the site and author:

> David Fremlin, *Knots and their symmetries*,
> https://david.fremlin.de/knots/

Do not attribute these Fourier series to Brian Gilbert / Knot Atlas ideal
databases; those are a different upstream (see Ideal_Sources).

---

## 4. What was removed from Knots_FourierSeries

The following directories were **not** Fremlin and were deleted from
`SSTcore/resources/Knots_FourierSeries` and the Workbench KnotPlot mirror:

- `9_2/`, `10_1/` — converted from Gilbert ideal.txt
- `1_1/` — hand-written unknot circle
