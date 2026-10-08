# A058 v0.1.1 validation record

Build date: 2026-10-07

## Static input audit

- 50 uploaded KnotPlot scripts ingested unchanged.
- Composition: 20 knot, 16 link, 14 torus scripts.
- Every script has 15 `ago 1000` relaxation increments and 16 saves including the initial state.
- Bead counts: 25 scripts at 300, 15 at 600, 10 at 900.
- Main historical settings are constant across all 50 scripts.
- No historical save explicitly pins `ascii/raw`.
- None of the 50 scripts explicitly sets `charge`, `hooke`, `power`, or `timeincr`.

## Package validation

- Python source compilation: PASS.
- Local unit tests (`tests/test_audit.py`, `tests/test_metrics.py`): **2 passed**.
- Smoke campaign generation: 25 conditions.
- Pilot campaign generation: 150 conditions.
- Synthetic parser/shape-analysis smoke: PASS; null-control geometry remained below numerical noise.
- Public blind-forbidden-term scan: PASS (zero hits outside `private/`).

## Native certification status

The C++/pybind11 source is included and G5 is fail-closed: it cannot PASS by falling back to Python. The build was not compiled in the artifact-construction container because `pybind11` was not installed and network package installation was unavailable. On the target Workbench machine, `run_install.cmd` installs the declared dependency and builds `kpmetrics_native`; G5 then performs strict Python-FP64 versus C++-FP64 parity at relative tolerance `1e-12`.

## KnotPlot runtime validation status

KnotPlot itself is not available in the artifact-construction environment. Therefore G2--G7 are intentionally unresolved until the supplied KnotPlot campaign is executed on the user's machine. This is by design: no synthetic substitute is allowed to certify those gates.

## v0.1.1 runtime-path hardening
The user-supplied Windows shortcut identified the expected KnotPlot target and Start-In directory. v0.1.1 converts those into runtime defaults without depending on the `.lnk` file. Campaign result paths are absolute in generated KnotPlot scripts, so the process working directory is no longer part of result-path semantics. The runner hashes the resolved `KnotPlot.exe` and writes the runtime decision to `campaign/runtime_<tier>.json`.

## Local validation performed in build environment
- Python syntax compilation: PASS for campaign generator, runner, experiment modules, and tests.
- Historical 50-script static audit unit check: PASS.
- Coordinate metric rigid-transform invariance unit check: PASS.
- v0.1.1 runtime resolver: PASS for explicit executable, `%USER_PROFILE%` executable discovery, and `outputs` Start-In selection.
- Campaign generator: PASS; generated KnotPlot scripts use absolute result paths.
- Full framework-driven pytest collection was not executable in the sandbox because the relative `.sst_framework_root` intentionally points to the target SST-Workbench v1.0.6 installation, which is absent here. The resolver failed closed as designed.
