@echo off
setlocal EnableExtensions
if "%~1"=="" (
  echo Usage: run_focus_topology.cmd ^<topology^> [--libraries=...] [--min-carriers=N] [--kind=knots^|links^|all]
  echo Example: run_focus_topology.cmd L2a1 --libraries=Gilbert,Katlas --min-carriers=2 --kind=links
  exit /b 2
)
echo ============================================================
echo SST SC-II Modal Phase Clock v0.1.1 - topology focus
echo Command line: %*
echo ============================================================
call run_setup.cmd || exit /b 1
call run_build_native.cmd || exit /b 1
call run_selftest.cmd || exit /b 1
call .venv\Scripts\activate.bat || exit /b 1
.venv\Scripts\python.exe -m sst_modal_clock.focus_runner %*
exit /b %ERRORLEVEL%
