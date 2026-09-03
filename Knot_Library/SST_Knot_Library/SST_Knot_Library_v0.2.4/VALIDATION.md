# Validation — SST Knot Library v0.2.4

Release-side validation performed 2026-08-30.

## Python

`PYTHONPATH=. python tests/test_smoke.py`

Result: **25/25 PASS**.

Coverage includes geometry/resampling, S3 round-trip, Bishop thread bundles, self-linking, KAtlas registry
integrity, braid component counts, Hopf-link linking, standard/commented/4VECT, Ridgerunner auxiliary-VECT
exclusion, KnotPlot LOCD, Brian Gilbert Fourier, TwelveData metadata handling, topology namespaces, blind
byte commitments, release identity, source catalog integrity, broad-project scanner trust and ignored-file
examples.

## Reference suite

`PYTHONPATH=. python tests/validate_reference_cases.py`

Result: PASS; `library_version = 0.2.4`.

## C++17/OpenMP

`g++ -std=c++17 -O2 -fopenmp cpp/selftest.cpp`

Result: PASS (`circle_writhe = 0`).

The decisive Windows MSVC/CPython pybind/OpenMP validation remains `run_all.cmd` on the target machine.
The full script requires native backend import, OpenMP and matching `RELEASE.json` identity.

## User v0.2.3 output audit motivating v0.2.4

- `KnotPlot\knots\final`: 49/49 `OK`.
- `Knot_Library\Sources`: 53 `OK`, 1 `SKIPPED_METADATA`, 0 `ERROR`.
- `KnotPlot\knots`: 1177 `OK`, 2200 `ERROR`; every error was VECT-related. Exactly 1907 failed on
  a literal `#` token and 293 were `*.struts.vect` files with no centerline component of >=3 points.
- broad `KnotPlot`: 9855 `OK`, 2777 `SKIPPED_NON_GEOMETRY`, 2897 `ERROR`; every error was VECT-related.
  Exactly 2544 failed on `#`, while 353 were `*.struts.vect`.
- `Fremlin_FourierSeries`: 402 files discovered; ignored extensions included 88 `.jpeg`, 76 `.scad`,
  76 `.short`, 75 `.stl`, and **73 `.fseries`**. No `.fseries` parser is enabled without a verified syntax sample.

The VECT parser change is grounded in the documented Geomview/plCurve VECT syntax, where plCurve is the
polygon library used by Ridgerunner. Auxiliary strut/gradient files remain outside the centerline trust boundary.
