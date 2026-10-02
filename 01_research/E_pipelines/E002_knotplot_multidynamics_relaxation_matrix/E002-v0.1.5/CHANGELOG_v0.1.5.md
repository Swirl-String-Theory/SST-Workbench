# CHANGELOG v0.1.5

## KnotPlot catalogue/read-path resolver

The v0.1.4 preflight proved that output creation worked but `load 3.1` loaded
nothing. KnotPlot documents `load filename` as a file load and the standard knot
catalogue as files in the distribution's `basic` directory. In batch mode the
shortcut working directory does not necessarily expose that read path.

### Changes
- Adds `knotplot_runtime.py`.
- Starts batch KnotPlot using documented `-nographics -stdin`.
- Captures `version` and `path` into `preflight/00_runtime_info.log`.
- Locates the installed KnotPlot `basic` catalogue directory.
- Resolves `3.1` to the actual catalogue file and probes that explicit file.
- Discovery source scripts keep readable `load 3.1`, while runtime scripts receive
  `load C:/.../basic/3.1`.
- Applies the same catalogue-ID resolution to catalog runtime scripts.
- Catalog output paths are now version-independent (`__MATRIX_ROOT__`).
- Repairs `run_catalog_batch.py` for the strict v0.1.4 runner API.
- Adds `run_runtime_diagnostic.cmd`.

No scientific sweep values or recipe-selection gates changed.
