@echo off
setlocal
set "HERE=%~dp0"
if "%~2"=="" (
  echo Usage: run_dual.cmd "FULL_A075_VERSION_PATH" "FULL_A077_VERSION_PATH"
  exit /b 2
)
set "PYTHONPATH=%HERE%;%PYTHONPATH%"
python -m resolver.campaign --a075-root "%~1" --a077-root "%~2" --grids 48 64 80 96 --time 0.02 --dt 0.001 --markers 12 --output-parent "%HERE%.."
exit /b %errorlevel%
