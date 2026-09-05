# CHANGELOG v0.3.1

## Critical directory-bootstrap fix

The v0.3.0 campaign generated all 181 KPC candidates correctly, but every run
failed when KnotPlot tried to write the first checkpoint:

```text
can't open file `.../out/probe/<candidate>_i00000.k'
can't open file `.../out/probe/<candidate>_i00000.txt'
```

Cause: `out/probe`, `out/extended`, and other runtime directories were empty in
the release tree. ZIP archives do not reliably preserve empty directories, so
they were absent after extraction.

### Fixed
- `generate_kpc.py` creates the complete runtime directory tree.
- `run_stage.py` independently recreates the stage-specific runtime tree before
  invoking KnotPlot.
- `analyze.py` creates `analysis/` before writing.
- Added `filesystem_preflight.py` and `run_filesystem_preflight.cmd`.
- `run_all.cmd` now runs the filesystem writeability preflight first.
- Selftest now verifies all runtime directories exist and are writable.

### Scientific configuration
Unchanged:
- 45 parameter families
- 181 candidates per stage
- same trefoil 3.1 baseline
- same parameter ranges
- same i100 probe and i1000 extended design

Therefore the failed v0.3.0 run contains no parameter-effect result; it is an
infrastructure failure before the first checkpoint.
