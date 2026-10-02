# CHANGELOG v0.1.4

## Runtime-path + installed-KnotPlot preflight hotfix

### Fixed
- Discovery `.kpc` files no longer hard-code `...v0.1.0/out`.
- Source scripts now use `__MATRIX_ROOT__`; `run_matrix_batch.py` renders a
  temporary runtime script whose output path points to the CURRENT workmap.
- Expected-output auditing is performed against that rendered runtime script.
- A load/write preflight proves that `load 3.1`, `save`, and `coords` work before
  the 10-script campaign starts.
- The runner probes both `nbeads 300` and `refine nbeads 300`, then selects the
  syntax actually accepted by the installed KnotPlot executable.
- Strict failures now include exact KnotPlot log line numbers and text.

### Why
v0.1.3 was executed from a folder named `...v0.1.3`, while all discovery
scripts still saved to `...v0.1.0/out`. KnotPlot could therefore exit with code
0 while failing to create the requested files.

### Scientific design
Unchanged:
DISCOVERY on knot 3.1 -> analyze parameter effects -> select/approve recipe ->
apply approved recipe to the catalog.
