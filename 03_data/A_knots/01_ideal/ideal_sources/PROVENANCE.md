# Data provenance policy — SST-Workbench

**Status:** working policy, proposed for canonisation as a companion to
`CANON_SOURCE_HIERARCHY.md`.
**Scope:** every externally sourced numerical dataset used anywhere in the SST
corpus, and every file derived from one.

---

## 0. The problem this solves

Three provenance failures have already occurred in this project and all three
were invisible to a per-file checksum:

1. A manuscript described the ideal-trefoil Fourier record as having
   "unresolved public-redistribution status" while the canon cited a different
   paper as its certified source.
2. `SSTcore`'s bundled `ideal.txt` turned out to contain **13 records that are
   not in the upstream file at all**, four of which appear in no Knot Atlas
   file whatsoever.
3. A `.gz` re-download produces a different container hash for identical
   content, because gzip embeds an mtime — so "the checksum changed" carries
   no information unless you know which layer was hashed.

The policy below makes each of these mechanically detectable.

---

## 1. Directory layout

Working archive (flat; used today):

```
SST-Workbench/Ideal_Sources/       # immutable upstream bytes + provenance docs
  Ideal.txt.gz
  Ideal_11a.txt.gz
  Ideal_11n.txt.gz
  IdealLinks.txt.gz
  IdealLinks_10a.txt.gz
  IdealLinks_10n.txt.gz
  IdealLinks_11a1.txt.gz
  IdealLinks_11a2.txt.gz
  IdealLinks_11n1.txt.gz
  IdealLinks_11n2.txt.gz
  TwelveData.zip
  TwelveSummary.zip
  0TwelveData.csv
  SOURCE.md
  MANIFEST.json                    # generated; commit after init
  PROVENANCE.md
  sst_provenance.py
```

Canonical long-term sketch (same policy; nested by upstream date when migrated):

```
SST-Workbench/
  data/
    upstream/                      # immutable. Never edited, never normalised.
      knotatlas/
        <upstream-date>/
          Ideal.txt.gz … IdealLinks_11n2.txt.gz
          TwelveData.zip
          TwelveSummary.zip
          0TwelveData.csv
      SOURCE.md
      MANIFEST.json
    derived/
      <artifact-name>/
        RECIPE.json
        …
    tools/
      sst_provenance.py
```

Rules:

- **Upstream data is read-only.** Files land there exactly as downloaded,
  compression intact. No gunzip/unzip-to-replace, no line-ending conversion,
  no reformatting, no merging. Anything a tool cannot read in that form is
  the tool's problem.
- **Every consumer reads from Ideal_Sources (or `data/upstream/`) or from a
  `derived/` artifact with a `RECIPE.json`.** Nothing reads from a loose copy.
- **The nested directory name is the upstream date, not the download date.**
  The download date lives in `SOURCE.md` and in `MANIFEST.generated_utc`.

---

## 2. Three hash levels

`MANIFEST.json` records all three for every payload. They answer different
questions and conflating them is what caused failure (3) above.

| Field | What it hashes | Use it to answer |
|---|---|---|
| `sha256_container` | the file on disk, `.gz`/`.zip` and all | "is this the exact artifact I downloaded?" |
| `sha256_payload` | decompressed bytes, byte-for-byte as upstream serves them | **"is this the citable dataset?"** — quote this in manuscripts |
| `sha256_canonical` | payload with CR/CRLF→LF, per-line trailing whitespace stripped, one terminating LF | "is the *content* the same, ignoring platform transfer damage?" |

`verify` reports three outcomes accordingly:

```
OK    payload byte-identical
OK*   payload identical, container recompressed        (expected for .gz)
EOL   identical only after normalisation — NOT citable as the original
```

An `EOL` result is not a failure, but a file in that state **may not be quoted
as the upstream artifact**. It is a derived file and belongs in `derived/`.

---

## 3. Record-level hashing

For the Fourier record files the manifest also stores a canonical hash **per
record** (`<AB Id=…>`, `<TL Id=…>`, `<HT Id=…>`).

This is the part that matters for publication. The entire ropelength strand of
SST rests on one record, `3:1:1`. Citing a 5 MB file hash proves nothing about
that record; citing the record hash proves everything:

```
$ sst_provenance.py cite data/upstream/MANIFEST.json 3:1:1
record   3:1:1
file     knotatlas/2016-11/ideal.txt.gz::ideal.txt
payload  sha256:7c0597d27a99df20d514730f6ec89c572c77e627ff821f46d42a783a778e90eb
record   sha256:ec07ca79b05258fdfe2569a42975ed752b5843b291f4219ebdb79c717d5fd250
dataset  Database of Ideal Knots 3-10 crossings -- Brian Gilbert (6/11/2016 2:12:11 p.m.)
upstream ideal.txt mtime 2016-11-06T01:12:25+00:00
```

That block is what goes in a manuscript's data-availability statement.

---

## 4. Attribution comes from the file, not from memory

All four Knot Atlas record files carry a `<DATA>` header, which the manifest
captures verbatim:

| File | Title | Author | Date |
|---|---|---|---|
| `ideal.txt` | Database of Ideal Knots 3-10 crossings | Brian Gilbert | 6/11/2016 |
| `idealLinks.txt` | Database of Ideal Links 2-9 crossings | Brian Gilbert | 6/11/2016 |
| `ideal_11a.txt` | Database of Ideal Knots K11a | Brian Gilbert | 7/11/2016 |
| `ideal_11n.txt` | Database of Ideal Knots K11n | Brian Gilbert | 7/11/2016 |

**Rule:** cite the `<DATA>` attribution. Do not substitute a paper that
computed *a* ropelength for the same knot type unless you are using that
paper's numbers. Attributing these records to a Ridgerunner publication is a
provenance error, because the records are not that publication's output and do
not carry its rigorous bounds.

---

## 5. Derived artifacts

Anything that is not a byte-for-byte upstream file goes in `derived/` with a
`RECIPE.json`:

```json
{
  "schema": "sst-provenance-recipe/1",
  "name": "ideal-lf-augmented",
  "inputs": [
    {"file": "knotatlas/2016-11/ideal.txt.gz",
     "member": "ideal.txt",
     "sha256_payload": "7c0597d2…"}
  ],
  "operations": [
    "CRLF -> LF",
    "append 13 records: 0:1:1, 0:1:2, 2:2:1, 6:2:3, K11a247, K11a367, L2a1, L4a1, L5a1, L6a1, L6a4, L6n1, L8a1"
  ],
  "record_provenance": {
    "K11a247": "knotatlas/2016-11/ideal_11a.txt.gz::ideal_11a.txt",
    "L2a1":    "knotatlas/2016-11/idealLinks.txt.gz::idealLinks.txt",
    "0:1:1":   "UNKNOWN — no Knot Atlas source",
    "0:1:2":   "UNKNOWN — no Knot Atlas source",
    "2:2:1":   "UNKNOWN — no Knot Atlas source",
    "6:2:3":   "UNKNOWN — no Knot Atlas source"
  },
  "epistemic_label": "[DERIVED — mixed provenance; four records UNRESOLVED]"
}
```

A derived file with any `UNKNOWN` entry **must not be used as a numerical
source for a canon claim** until the entry is resolved or the record is
removed.

---

## 6. Verification in CI

```bash
python data/tools/sst_provenance.py verify data/upstream -m data/upstream/MANIFEST.json
```

Exit code 1 on any failure. Run it in CI and before any canon patch that
touches a numerical value sourced from these files.

---

## 7. Known convention facts (verified, keep here so they are not re-derived)

- The `D` attribute in these files is the **tube diameter**. Confirmed against
  the one exactly-known configuration: `L2a1` is two unit circles with centres
  separated by 1, minimum centreline distance exactly 1.000000,
  `khat_max = 1.0000`, Gauss linking number −1.000000 exactly.
- Consequently `ropelength_radius = 2 × (L/D)`. For `L2a1`: `L/D = 4π = 12.566`
  and `L/a = 8π = 25.133`, the latter matching Cantarella–Kusner–Sullivan's
  chain formula `(4π+4)k − 8` at `k = 2`.
- The same factor-2 convention holds for `0TwelveData.csv`: for `12a1`, the
  120-vertex polyline has length 53.58479 and the CSV lists 107.17451, i.e.
  `2 × L`, agreeing to 46 ppm (the residual is the polygonal-vs-smooth gap at
  120 vertices).
- The Fourier evaluation convention is `γ(t) = A₀/2 + Σ_{n≥1} (Aₙ cos nt + Bₙ sin nt)`.
  Using `A₀` instead of `A₀/2` translates each component by `A₀/2`, which is a
  *relative* shift between components of a link and silently corrupts every
  inter-component distance while leaving lengths, curvatures and linking
  numbers correct. Any tool reading these files must be tested on a link whose
  components have `A₀ ≠ 0` — `L4a1` has `A₀ = 0` and will pass either way.
