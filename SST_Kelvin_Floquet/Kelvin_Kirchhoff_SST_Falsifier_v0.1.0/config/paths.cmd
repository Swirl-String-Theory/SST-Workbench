@echo off
set "KK_ROOT=%~dp0.."
for %%I in ("%KK_ROOT%") do set "KK_ROOT=%%~fI"
if not defined SST_KNOTS_DIR set "SST_KNOTS_DIR=%KK_ROOT%\..\..\KnotPlot\knots\final"
if exist "%KK_ROOT%\..\..\.venv\Scripts\python.exe" (
  set "KK_PY=%KK_ROOT%\..\..\.venv\Scripts\python.exe"
) else if exist "%KK_ROOT%\.venv\Scripts\python.exe" (
  set "KK_PY=%KK_ROOT%\.venv\Scripts\python.exe"
) else (
  set "KK_PY="
)
