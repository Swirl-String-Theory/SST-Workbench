# Build validation — v0.2.0

Artifact-generation validation date: 2026-09-04.

## Static/runtime checks performed

- `python -m compileall -q sst_qgi tests`: **PASS**.
- `python -m unittest discover -s tests -v`: **15/15 PASS**.
- Raw-population synthetic calibration test: phase reconstruction recovers the preregistered cubic scale within test tolerance.
- Raw velocity-loop circulation quadrature test: **PASS**.
- Rankine identities:
  - \(\hbar/M=\Gamma/(4\pi)\): **PASS**;
  - \(h/M=\Gamma/2\): **PASS**;
  - \(h=2\pi\hbar\): **PASS**.
- Integrated synthetic end-to-end specific-action smoke:
  `PROVENANCE_CLEAN_SPECIFIC_ACTION_PASS`.
  The synthetic smoke files are **not shipped** and cannot contribute to a scientific run.
- Empty-external-data smoke:
  - macro action/gauge gates: **PASS**;
  - QGI data: `NOT_RUN`;
  - fluid circulation: `NOT_RUN`;
  - primary G10: `NOT_RUN`;
  - verdict: `STRICT_MACRO_PASS__QGI_PHASE_DATA_NOT_AVAILABLE`.
- Stale prepared-fluid state guard tested/fixed: deleting raw/provenance inputs invalidates prior prepared circulation.
- Blind target-leak scan: **PASS**.
- Separate reveal-target workflow: **PASS**.
- Shareable BLIND/REVEALED packaging excludes the private HMAC reveal secret.
- Shader-derived 48-candidate sweep retained.
- Relaxed-knot path remains `..\..\KnotPlot\knots\final`.
- Dataset ingest audit now separates discovered/accepted/rejected/skipped files.
- setuptools explicit package discovery retained.
- MSVC `py::ssize_t` portability fix retained.
- Visual Studio 2022 and 2026 Community/BuildTools fallback paths retained.

## Public QGI figure fallback

The package contains a fixed-source acquisition/digitization stage but does not ship a copy of the QGI paper.
The artifact container could not download the public PDF through its file-download runtime, so the actual-PDF
pixel extraction was not executed locally. The axes calibration was checked against the rendered published
Fig. 2 and Fig. 3 pages. On failure of Fig. 2 population extraction, the code falls back to the Fig. 3
experimental-data fit and marks the result `CONDITIONAL`.

No digitized public-figure result can be promoted to author/raw grade.

## Native backend

The artifact-generation environment did not have pybind11 installed in its system Python, so the Windows
native extension was not compiled here. The full Windows `run_all.cmd` requires the native extension and
contains the previously validated VS2022/VS2026 discovery strategy.
