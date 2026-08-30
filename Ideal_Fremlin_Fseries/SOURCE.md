# Upstream source — David Fremlin knot Fourier series and 3D realizations

Retrieved by: O. Iskandarani
Retrieval date: 2026-08-28
Origin: https://david.fremlin.de/knots/ (David Fremlin, *Knots and their symmetries*)

This directory holds a byte-for-byte local mirror of the downloadable assets
linked from each knot page on that site (from knot 3₁ through 15331):

| Kind | Extension | Role |
|---|---|---|
| Fourier series | `.fseries` | coordinate Fourier coefficients on [-π, π] |
| Point lists | `.short` | coordinates along the path |
| OpenSCAD | `.scad` | solid model source |
| STL | `.stl` | triangle mesh |
| Images | `.jpeg` / `.jpg` / `.png` | page figures (including variants) |

Layout: `fremlin/<knot_id>/<basename>` where `<knot_id>` is the page stem
(`3_1`, `12a_1202`, `15331`, …). Variant realizations keep Fremlin’s suffixes
(`u`, `p`, `d`, `r`, `z`, …) in the filename.

Re-fetch with:

```
python download_fremlin_knots.py --out fremlin
python sst_provenance.py init fremlin -o MANIFEST.json --source SOURCE.md --no-records
python sst_provenance.py verify fremlin -m MANIFEST.json
```

Attribution: cite David Fremlin and https://david.fremlin.de/knots/. See
PROVENANCE.md.

Licence / redistribution status: **UNRESOLVED.** Do not redistribute these
files as journal supplementary material until clarified. Ship the manifest and
the reconstruction script instead; both are sufficient for a referee to
reproduce the tree.
