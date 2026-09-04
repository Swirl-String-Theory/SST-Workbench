# Build validation — v0.1.1

Artifact-generation validation date: 2026-09-03.

Validation performed:

- `python -m compileall -q sst_qgi tests`: **PASS**;
- `python -m unittest discover -s tests -v`: **8 passed**;
- Python-fallback blind prepare → BASIC → EXTENDED → BLIND package: **PASS**;
- blind verdict: `STRICT_TARGET_BLIND_MACRO_ACTION_PASS`;
- blind reveal-target leak gate: **PASS**;
- legacy near-\(h\) value classification: `ALGEBRAIC_ECHO_CONTROL`;
- `independent_prediction = false` verified in blind output;
- separate reveal-target smoke: **PASS**;
- revealed Planck-provenance gate: `NOT_QUALIFIED`, intentionally;
- no synthetic QGI phase dataset is shipped;
- shader-derived family retained as a first-class source;
- relaxed dataset remains auto-discovered at `..\..\KnotPlot\knots\final`;
- setuptools flat-layout package-discovery fix included;
- MSVC global `ssize_t` portability issue fixed with `py::ssize_t`.

The artifact container lacks the user's external relaxed-knot directory, so the smoke used
the 48 built-in shader-derived candidates plus one control. On the user's workstation the
relaxed source is expected to be added automatically, as in v0.1.0.

## Native backend

The Windows full run still requires C++17/pybind11. The source includes both previously
identified Windows fixes. The local artifact smoke used the NumPy fallback because this
execution environment did not build the Windows MSVC extension.
