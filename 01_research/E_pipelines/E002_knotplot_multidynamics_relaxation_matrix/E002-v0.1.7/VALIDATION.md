# VALIDATION

Static release validation:

- 41 design entries preserved.
- `parameters_full_source.txt` confirms all 14 core runtime parameter names.
- `charge`, `hooke`, `power`, `tinc` are assignments (`=`), never action commands.
- `timeincr` is absent from generated KPC.
- `refine nbeads 300` is mandatory.
- `alex` is absent.
- each ordinary candidate includes i00000/i01000/i04000/i10000.
- save/coords parent directories are created by the runner.
- runtime logs hard-fail on `unknown command`, `obsolete`, missing output or file-open errors.

Real KnotPlot execution is intentionally performed on the target Windows installation.
