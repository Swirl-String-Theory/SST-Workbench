# Upstream source — Knot Atlas ideal knot/link databases

Retrieved by: O. Iskandarani  
Origin: https://katlas.org/wiki/Ideal_knots (The Knot Atlas)

Retrieval:

| Batch | Date | Contents |
|---|---|---|
| Initial | 2026-08-04 | Ideal*.gz (knots 3–11), IdealLinks.txt.gz, 0TwelveData.csv |
| Extension | 2026-08-28 | IdealLinks_10*/11*.gz; TwelveData.zip; TwelveSummary.zip |

Containers are **unmodified upstream bytes** (no gunzip, unzip-to-disk, EOL rewrite, or re-compress).

## Inventory

| File | Media / role | Notes |
|---|---|---|
| `Ideal.txt.gz` | [Media:Ideal.txt.gz](https://katlas.org/images/d/d2/Ideal.txt.gz) | knots 3–10, `<AB>` (Brian Gilbert) |
| `Ideal_11a.txt.gz` | [Media:Ideal_11a.txt.gz](https://katlas.org/images/4/42/Ideal_11a.txt.gz) | 11-crossing alternating, `<HT>` |
| `Ideal_11n.txt.gz` | [Media:Ideal_11n.txt.gz](https://katlas.org/images/8/85/Ideal_11n.txt.gz) | 11-crossing non-alternating, `<HT>` |
| `IdealLinks.txt.gz` | [Media:IdealLinks.txt.gz](https://katlas.org/images/5/5a/IdealLinks.txt.gz) | links 2–9, `<TL>` |
| `IdealLinks_10a.txt.gz` | [Media:IdealLinks_10a.txt.gz](https://katlas.org/images/e/ec/IdealLinks_10a.txt.gz) | 10-crossing alternating links |
| `IdealLinks_10n.txt.gz` | [Media:IdealLinks_10n.txt.gz](https://katlas.org/images/d/de/IdealLinks_10n.txt.gz) | 10-crossing non-alternating links |
| `IdealLinks_11a1.txt.gz` | [Media:IdealLinks_11a1.txt.gz](https://katlas.org/images/f/f3/IdealLinks_11a1.txt.gz) | L11a1–L11a300 |
| `IdealLinks_11a2.txt.gz` | [Media:IdealLinks_11a2.txt.gz](https://katlas.org/images/9/99/IdealLinks_11a2.txt.gz) | L11a301–L11a548 |
| `IdealLinks_11n1.txt.gz` | [Media:IdealLinks_11n1.txt.gz](https://katlas.org/images/2/26/IdealLinks_11n1.txt.gz) | L11n1–L11n230 |
| `IdealLinks_11n2.txt.gz` | [Media:IdealLinks_11n2.txt.gz](https://katlas.org/images/b/bb/IdealLinks_11n2.txt.gz) | L11n231–L11n459 |
| `TwelveData.zip` | [File:TwelveData.zip](https://katlas.org/wiki/File:TwelveData.zip) | 2176 polyline files + `0TwelveData.csv` (12 crossings; Ridgerunner / Klotz) |
| `TwelveSummary.zip` | [File:TwelveSummary.zip](https://katlas.org/wiki/File:TwelveSummary.zip) | compact 12-crossing summary companion (`0TwelveData.csv`) |
| `0TwelveData.csv` | standalone copy | 2176 rows; also a member of both Twelve* zips |

Attribution: Gilbert Fourier record files carry `<DATA … Author="Brian Gilbert" …>`. Cite that header. Twelve-crossing polylines: Alex Klotz / Caleb Anderson (Ridgerunner), Se-Goo Kim coordinates — see the Ideal knots wiki page. See PROVENANCE.md §4.

Licence / redistribution status: **UNRESOLVED.** Do not redistribute these
files as supplementary material to a journal until clarified. Ship the
manifest and the reconstruction code instead; both are sufficient for a
referee to reproduce every number.
