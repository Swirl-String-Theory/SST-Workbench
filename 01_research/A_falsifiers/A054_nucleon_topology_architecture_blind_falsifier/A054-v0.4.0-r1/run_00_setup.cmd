@echo off
setlocal EnableExtensions
for %%I in ("%~dp0.") do set "ROOT=%%~fI"
set "WB=%~1"
if "%WB%"=="" if not "%SST_WORKBENCH_ROOT%"=="" set "WB=%SST_WORKBENCH_ROOT%"
if "%WB%"=="" set "WB=C:\workspace\projects\SST-Workbench"
set "FW=%WB%\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.4"
set "PY=%ROOT%\.venv\Scripts\python.exe"

if not exist "%FW%\PACKAGE_MANIFEST.json" (
  echo [ERROR] Framework v1.0.4 not found: %FW%
  endlocal & exit /b 2
)
if not exist "%FW%\profiles\multilibrary_gpu.toml" (
  echo [ERROR] Canonical framework profile missing: %FW%\profiles\multilibrary_gpu.toml
  echo [ERROR] Do not add an A054-specific profile to the frozen framework; restore the canonical v1.0.4 tree.
  endlocal & exit /b 3
)

if not exist "%PY%" (
  py -3 -m venv "%ROOT%\.venv"
  if errorlevel 1 (set "RC=%ERRORLEVEL%" & endlocal & exit /b %RC%)
)

"%PY%" -m pip install -U pip setuptools wheel pybind11 numpy pytest
if errorlevel 1 (set "RC=%ERRORLEVEL%" & endlocal & exit /b %RC%)

rem Install framework and instance separately so a bad path cannot be hidden by the next command.
"%PY%" -m pip install --no-build-isolation -e "%FW%"
if errorlevel 1 (set "RC=%ERRORLEVEL%" & endlocal & exit /b %RC%)
"%PY%" -m pip install --no-build-isolation -e "%ROOT%"
if errorlevel 1 (set "RC=%ERRORLEVEL%" & endlocal & exit /b %RC%)

set "SST_FALSIFIER_FRAMEWORK_ROOT=%FW%"
"%PY%" "%ROOT%\run_instance.py" SELFTEST
set "RC=%ERRORLEVEL%"
endlocal & exit /b %RC%
