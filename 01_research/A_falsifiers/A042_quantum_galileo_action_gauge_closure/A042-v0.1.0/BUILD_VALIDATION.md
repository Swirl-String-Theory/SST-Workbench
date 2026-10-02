# Build validation

Artifact-generation validation date: 2026-09-03.

Validation performed on the generated source tree:

- `python -m unittest discover -s tests -v`: **7 passed**;
- `python -m compileall -q sst_qgi tests`: **PASS**;
- complete Python-fallback blind → BASIC → EXTENDED → reveal → package smoke: **PASS**;
- smoke blind verdict: `BLIND_MACRO_CLOSURE_PASS`;
- smoke reveal verdict: `DATASET_INCOMPLETE__RELAXED_SOURCE_MISSING`, as expected because the
  artifact container does not contain the user's external `KnotPlot\knots\final` dataset;
- reveal-key commitment verification: **PASS**;
- private secret excluded from both shareable archives: **PASS**;
- 48 built-in shader-derived candidates configured (3 × 4 × 4);
- the historical track-trefoil example
  `baseR=4.08248290463863`, `bulge_R=2.2`, `z_weave=3.0`
  is included exactly;
- canonical SST action quantum:
  \(h_{\rm SST}=6.6260695156810226\times10^{-34}\ {\rm J\,s}\);
- output paths use the project-specific output convention;
- separate BLIND / REVEALED packaging paths are defined.

## Native backend

The source includes a C++17/pybind11 backend and Windows build script.
The artifact container does not have `pybind11` installed in its system Python, so native
compilation was not executed here. `run_01_install.cmd` installs `pybind11` from
`requirements.txt`, after which `run_02_build_native.cmd` requires and verifies the native
module. A native-build failure stops `run_all.cmd`; it does not silently downgrade the
Windows full run to Python.
