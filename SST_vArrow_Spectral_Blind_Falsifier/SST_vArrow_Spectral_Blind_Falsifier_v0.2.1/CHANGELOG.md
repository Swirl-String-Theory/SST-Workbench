# Changelog

## v0.2.1

Windows wrapper / recursive-discovery hotfix.

- `run_scan.cmd` now returns exit code 0 after a successful scan.
- Removed all dependence on `activate.bat`; every wrapper calls `.venv\\Scripts\\python.exe` and `pytest.exe` directly.
- `run_install.cmd` uses quoted absolute venv paths and checks every install step.
- Added `run_scan_workspace.cmd`, which defaults to scanning `..\\..` (normally the SST-Workbench root from this package layout).
- Workspace scans ignore `.venv`, Git/cache/build folders and this falsifier's own generated output folders, while still allowing output folders from other SST workbenches to be discovered.
- Existing recursive `campaigns\\` behavior and blind/unblind logic are unchanged.

## v0.2.0

- Added recursive campaign discovery under `campaigns/`.
- Added VortexLab scalar diagnostic-log parser and `diagnostic_only` classification.
- Added imported Library excerpt and provenance notes.
- Added automatic generated manifest and scan audit.
