# A058 v0.2.0 — Trefoil Default-Relative Strength Response

Single-topology follow-up to A058-v0.1.x. Only the catalogue trefoil is used. Positive strength multipliers follow `m=2^(k/4)`, `k=-16..16`, plus an exact zero endpoint. Non-strength relaxation controls are left at KnotPlot `reset all` defaults. The conditional third strength axis is enabled only because its force is reset-all-disabled.

## Install test
`run_install.cmd` now performs unit/native tests and then launches KnotPlot once to create **exactly one** ASCII trefoil export with no relaxation. This verifies executable discovery, batch stdin, catalogue load, 300-bead refinement, and ASCII save before a scientific campaign can start.

## Full campaign
`run_pilot_all.cmd` performs install + one-export integration test, generates 101 scientific conditions, SELFTEST, FREEZE, KnotPlot acquisition, and FULL analysis.

KnotPlot is auto-discovered from `KNOTPLOT_EXE`, `%USER_PROFILE%\AppData\Local\Programs\KnotPlot\KnotPlot.exe`, or `%USERPROFILE%\AppData\Local\Programs\KnotPlot\KnotPlot.exe`. Start-In defaults to `%SST_WORKBENCH%\04_tools\A_geometry\A001_knotplot\` when available.
