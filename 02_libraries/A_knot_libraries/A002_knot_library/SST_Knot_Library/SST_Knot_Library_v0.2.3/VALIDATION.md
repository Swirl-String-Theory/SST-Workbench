# Validation — SST Knot Library v0.2.3

Release-side validation performed 2026-08-30.

## Python

`PYTHONPATH=. python tests/test_smoke.py`

Result: **23/23 PASS**.

Coverage includes geometry/resampling, S3 round-trip, Bishop thread bundles, self-linking,
KAtlas registry integrity, braid component counts, Hopf-link linking, VECT, KnotPlot LOCD,
Brian Gilbert Fourier, TwelveData metadata handling, topology namespaces, blind byte commitments,
release identity, source catalog integrity and the v0.2.3 scanner trust rules.

## Reference suite

`PYTHONPATH=. python tests/validate_reference_cases.py`

Result: PASS; `library_version = 0.2.3`.

## C++17/OpenMP

`g++ -std=c++17 -O2 -fopenmp cpp/selftest.cpp`

Result: PASS (`circle_writhe = 0`).

The decisive Windows MSVC/CPython pybind/OpenMP validation remains `run_all.cmd` on the target machine.
The full script requires native backend import, OpenMP and matching `RELEASE.json` identity.

## User v0.2.2 dataset evidence motivating v0.2.3

- `KnotPlot\\knots\\final`: 49 selected, 49 `OK`, 0 `ERROR`.
- `Knot_Library\\Sources`: 54 selected, 53 `OK`, 1 `SKIPPED_METADATA`, 0 `ERROR`.
- broader KnotPlot project roots produced thousands of parse errors because v0.2.2 treated every
  selected text/CSV file as geometry; v0.2.3 classifies unrelated project text separately.
- `Fremlin_FourierSeries`: v0.2.2 selected zero files. v0.2.3 reports total discovered files and ignored
  extension counts, allowing the missing adapter/extension to be identified without guessing.
