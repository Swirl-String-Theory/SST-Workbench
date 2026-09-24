@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "WORKBENCH=%~1"
if not defined WORKBENCH for %%I in ("%CD%\..\..\..\..") do set "WORKBENCH=%%~fI"
set "OUTPUT=%CD%\E010_PKLSA_Production_Knot_Link_Basis_v0.3.0-outputs"
set "ARCHIVE_DIR=%CD%\.."

if not exist ".venv\Scripts\python.exe" (
  echo [FAIL] .venv not found. Run run_all.cmd once first.
  exit /b 2
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 exit /b %errorlevel%

echo ============================================================
echo  E010 PKLSA TARGETED FREMLIN a0 REPAIR
echo  Workbench : %WORKBENCH%
echo  Output    : %OUTPUT%
echo ============================================================
echo.

echo [00] Regression/package tests
python -m pytest -q
if errorlevel 1 goto :fail

echo.
echo [01] Verify source snapshot and rerun failed topologies only
python tools\repair_failed_fremlin_a0.py --workbench "%WORKBENCH%" --output "%OUTPUT%" --archive-dir "%ARCHIVE_DIR%"
if errorlevel 1 goto :fail

echo.
echo ============================================================
echo [OK] Targeted repair completed and atlas packaged.
echo ============================================================
exit /b 0

:fail
echo.
echo ============================================================
echo [FAIL] Targeted repair stopped fail-closed.
echo        Inspect the production output and repair_history folder.
echo ============================================================
exit /b 1
