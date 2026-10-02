# CHANGELOG v0.1.3

## Hotfix: Windows CMD line endings

Six v0.1.2 launchers were accidentally written with the literal character sequence `\r\n` instead of actual Windows CRLF line endings. On Windows this caused commands such as `run_static_audit.cmd` to echo their contents instead of executing the intended Python program.

Fixed launchers:

- `run_static_audit.cmd`
- `run_fresh_discovery.cmd`
- `run_analyze.cmd`
- `run_prepare_catalog.cmd`
- `run_catalog.cmd`
- `run_catalog_one.cmd`

Added `run_cmd_lineending_audit.cmd` to detect this packaging regression.

No scientific KPC logic, matrix design, recipe selection, or catalog propagation rules were changed.

## KP-alex.exe

`alex -1` is a KnotPlot topological diagnostic that evaluates the Alexander polynomial at -1 (the knot determinant). The target installation does not provide the external helper used by that diagnostic, so v0.1.2+ intentionally omits `alex -1` from the automated relaxation campaign. This does not affect the relaxation dynamics or XYZ output.
