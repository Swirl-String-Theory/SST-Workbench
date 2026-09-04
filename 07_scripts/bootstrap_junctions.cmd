@echo off
rem Rebuild the SP02 compatibility junction layer after a fresh clone.
rem See 10_docs/migration/junctions.md
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "WB_ROOT=%%~fI"

if not exist "%WB_ROOT%\.sst-workbench-root" (
  echo ERROR: not an SST-Workbench root: %WB_ROOT% 1>&2
  exit /b 1
)

where python >nul 2>&1
if errorlevel 1 (
  echo ERROR: python not on PATH 1>&2
  exit /b 1
)

echo bootstrap_junctions: create
python "%SCRIPT_DIR%junctions.py" --root "%WB_ROOT%" create %*
if errorlevel 1 exit /b 1

echo bootstrap_junctions: verify
python "%SCRIPT_DIR%junctions.py" --root "%WB_ROOT%" verify %*
if errorlevel 1 exit /b 1

echo bootstrap_junctions: ok
exit /b 0
