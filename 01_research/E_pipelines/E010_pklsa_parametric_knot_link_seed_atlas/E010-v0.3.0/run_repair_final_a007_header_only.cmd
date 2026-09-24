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
echo  E010 PKLSA FINAL A007 REPAIR / VERIFY (IDEMPOTENT)
echo  Workbench : %WORKBENCH%
echo  Output    : %OUTPUT%
echo ============================================================
echo.

echo [00] Regression/package tests
python -m pytest -q
if errorlevel 1 goto :fail

echo.
echo [01] Verify source snapshot and rerun remaining failed topology only
python tools\repair_failed_a007_header_only.py --workbench "%WORKBENCH%" --output "%OUTPUT%" --archive-dir "%ARCHIVE_DIR%"
if errorlevel 1 goto :fail

echo.
echo ============================================================
echo [OK] Final targeted repair completed and atlas packaged.
echo ============================================================
exit /b 0

:fail
echo.
echo ============================================================
echo [FAIL] Final targeted repair stopped fail-closed.
echo        Inspect FAILED_TOPOLOGIES.json and repair_history.
echo ============================================================
exit /b 1
