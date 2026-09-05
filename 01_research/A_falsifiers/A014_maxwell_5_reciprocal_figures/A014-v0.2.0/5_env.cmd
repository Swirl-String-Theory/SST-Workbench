@echo off
set "M5_ROOT=%~dp0"
for %%I in ("%M5_ROOT%..\..") do set "M5_WORKBENCH=%%~fI"
set "M5_VENV=%M5_WORKBENCH%\.venv"
set "M5_PY=%M5_VENV%\Scripts\python.exe"
if not exist "%M5_PY%" (
  echo [5_Maxwell] Shared venv not found: "%M5_VENV%"
  echo [5_Maxwell] Run 5_run_install.cmd first.
  exit /b 2
)
set "M5_KNOTS_DEFAULT=%M5_WORKBENCH%\KnotPlot\knots\final"
exit /b 0
