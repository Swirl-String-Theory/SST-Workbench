@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "DATASET=%~1"
if not defined DATASET (
  if exist "..\..\KnotPlot\knots\final" set "DATASET=..\..\KnotPlot\knots\final"
)
if not defined DATASET (
  if exist "..\KnotPlot\knots\final" set "DATASET=..\KnotPlot\knots\final"
)
if not defined DATASET (
  if exist "KnotPlot\knots\final" set "DATASET=KnotPlot\knots\final"
)
if not defined DATASET set "DATASET=data\sample_knots"

echo ============================================================
echo SST Six-Source Blind Falsifier v0.1.0
echo Dataset: %DATASET%
echo ============================================================

if not exist ".venv\Scripts\python.exe" (
  echo [1/6] Creating local virtual environment...
  where py >nul 2>&1
  if not errorlevel 1 (
    py -3 -m venv .venv
  ) else (
    python -m venv .venv
  )
  if errorlevel 1 goto :fail
) else (
  echo [1/6] Local virtual environment already exists.
)

set "PY=.venv\Scripts\python.exe"

echo [2/6] Installing/updating Python dependencies...
"%PY%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :fail
"%PY%" -m pip install -r requirements.txt
if errorlevel 1 goto :fail

echo [3/6] Building native C++/pybind11 backend...
"%PY%" -m native_ext.build_ext_if_needed --force --strict
if errorlevel 1 (
  echo.
  echo [ERROR] Native build failed. run_all.cmd intentionally requires C++ for the full dataset.
  echo         On Windows install/repair Visual Studio 2022 C++ Build Tools, then rerun.
  echo         For a slow Python-only smoke run use run_fallback_sample.cmd.
  goto :fail
)

echo [4/6] Preflight and native parity audit...
"%PY%" run_preflight.py --dataset "%DATASET%" --require-native
if errorlevel 1 goto :fail
"%PY%" run_native_audit.py --out outputs\native_audit_latest.json --strict
if errorlevel 1 goto :fail

echo [5/6] Running BASIC + EXTENDED blind campaigns...
"%PY%" run_all.py --dataset "%DATASET%" --require-native
if errorlevel 1 goto :fail

echo [6/6] COMPLETE.
echo Results are under: %~dp0outputs\run_all_YYYYMMDD_HHMMSS\
echo Physical hypothesis FAILs are expected scientific outcomes and do not abort the run.
exit /b 0

:fail
echo.
echo ============================================================
echo SST6 RUN FAILED - see the messages above.
echo ============================================================
exit /b 1
