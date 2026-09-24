@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

rem ============================================================
rem E010 PKLSA v0.3.0 -- source-native production atlas runner
rem Default Workbench root: C:\workspace\projects\SST-Workbench
rem Usage: run_all.cmd [WORKBENCH_ROOT]
rem ============================================================

set "WB=%~1"
if not defined WB set "WB=C:\workspace\projects\SST-Workbench"
set "OUT=%~dp0E010_PKLSA_Production_Knot_Link_Basis_v0.3.0-outputs"
set "ARCHIVE_DIR=%~dp0.."
set "CONTRACT=%~dp0configs\source_contract_production_v2.json"
set "CATALOG=%~dp0configs\source_catalog_production_v2.json"
set "POC_CFG=%~dp0configs\qualification_extended.json"
set "FULL_CFG=%~dp0configs\qualification_publication.json"

if not exist "%WB%\.sst-workbench-root" (
  echo [ERROR] Not an SST-Workbench root: "%WB%"
  echo         Expected marker: %WB%\.sst-workbench-root
  exit /b 2
)
if not exist "%CONTRACT%" (
  echo [ERROR] Missing %CONTRACT%
  exit /b 2
)
if not exist "%CATALOG%" (
  echo [ERROR] Missing %CATALOG%
  exit /b 2
)

where python >nul 2>&1
if errorlevel 1 (
  echo [ERROR] python.exe not found on PATH.
  exit /b 2
)

rem Bootstrap MSVC automatically when cl.exe is not already available.
where cl >nul 2>&1
if errorlevel 1 (
  set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
  if exist "!VSWHERE!" (
    for /f "usebackq tokens=*" %%I in (`"!VSWHERE!" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "VSROOT=%%I"
    if defined VSROOT if exist "!VSROOT!\VC\Auxiliary\Build\vcvars64.bat" call "!VSROOT!\VC\Auxiliary\Build\vcvars64.bat" >nul
  )
)

where cl >nul 2>&1
if errorlevel 1 (
  echo [ERROR] MSVC C++ build tools not found. Run this from an x64 Developer Command Prompt
  echo         or install the Visual Studio C++ build tools.
  exit /b 2
)

if not exist "%OUT%" mkdir "%OUT%"
if not exist "%OUT%\logs" mkdir "%OUT%\logs"

echo ============================================================
echo  E010 PKLSA PRODUCTION RUN
echo  Workbench : %WB%
echo  Output    : %OUT%
echo ============================================================

rem ---- 00: environment + editable Python install --------------
echo.
echo [00] Python environment / dependencies
call run_00_setup.cmd
if errorlevel 1 goto :fail

call .venv\Scripts\activate.bat
if errorlevel 1 goto :fail

python -m pip install -q pytest
if errorlevel 1 goto :fail

rem Force the current C++/pybind11 extension to be rebuilt in-place.
rem The source is compatible with classic MSVC /openmp; no /openmp:llvm is required.
echo.
echo [01] Native C++ build (forced, MSVC-compatible)
python setup.py build_ext --inplace --force
if errorlevel 1 goto :fail
python -c "from pklsa_builder import _native as n; print('[OK] pklsa_builder._native imported; openmp_enabled=', bool(n.openmp_enabled))"
if errorlevel 1 goto :fail

rem ---- 02: package regression tests ----------------------------
echo.
echo [02] Package tests
python -m pytest -q tests
if errorlevel 1 goto :fail

rem ---- 03: repository-native preflight -------------------------
echo.
echo [03] Production atlas: contract audit, deep source hash,
echo      trefoil POC, full knot/link qualification, packaging
python tools\run_production_atlas.py ^
  --workbench "%WB%" ^
  --output "%OUT%" ^
  --contract "%CONTRACT%" ^
  --source-catalog "%CATALOG%" ^
  --poc-config "%POC_CFG%" ^
  --full-config "%FULL_CFG%" ^
  --archive-dir "%ARCHIVE_DIR%" ^
  --deep-hash ^
  --resume
if errorlevel 1 goto :fail

echo.
echo ============================================================
echo [PASS] E010 PKLSA production basis completed.
echo        Release: %OUT%\RELEASE.json
echo        Atlas  : %OUT%\atlas\
echo        ZIP    : %ARCHIVE_DIR%\E010_PKLSA_Production_Knot_Link_Basis_v0.3.0-outputs.zip
echo ============================================================
exit /b 0

:fail
echo.
echo ============================================================
echo [FAIL] PKLSA stopped fail-closed. Inspect:
echo        %OUT%
echo No publication-ready claim is made for this run.
echo ============================================================
exit /b 1
