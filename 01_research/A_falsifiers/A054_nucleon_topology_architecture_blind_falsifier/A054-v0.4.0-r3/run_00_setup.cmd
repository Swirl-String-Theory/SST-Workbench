@echo off
setlocal EnableExtensions
for %%I in ("%~dp0.") do set "ROOT=%%~fI"
for %%I in ("%ROOT%\..") do set "FAMILY=%%~fI"
set "VENV=%FAMILY%\.venvs\A054-v0.4.0-r3"
set "PY=%VENV%\Scripts\python.exe"
set "WB=%~1"
if "%WB%"=="" if not "%SST_WORKBENCH_ROOT%"=="" set "WB=%SST_WORKBENCH_ROOT%"
if "%WB%"=="" set "WB=C:\workspace\projects\SST-Workbench"
set "FW=%WB%\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.4"

if not exist "%FW%\PACKAGE_MANIFEST.json" (
  echo [ERROR] Framework v1.0.4 not found: %FW%
  exit /b 2
)
if not exist "%FW%\profiles\multilibrary_gpu.toml" (
  echo [ERROR] Canonical framework profile missing: %FW%\profiles\multilibrary_gpu.toml
  exit /b 3
)

rem Migration: an in-instance venv is forbidden because blind scanning must not inspect site-packages.
if exist "%ROOT%\.venv" (
  echo [INFO] Removing legacy in-instance .venv; r3 uses %VENV%
  rmdir /s /q "%ROOT%\.venv"
  if exist "%ROOT%\.venv" exit /b 4
)
if not exist "%PY%" (
  if not exist "%FAMILY%\.venvs" mkdir "%FAMILY%\.venvs"
  py -3 -m venv "%VENV%"
  if errorlevel 1 exit /b 10
)

"%PY%" -m pip install -U pip setuptools wheel pybind11 numpy pytest
if errorlevel 1 exit /b %ERRORLEVEL%

del /q "%ROOT%\experiment\_native*.pyd" >nul 2>nul
del /q "%ROOT%\experiment\_native*.so" >nul 2>nul
if exist "%ROOT%\build" rmdir /s /q "%ROOT%\build"

"%PY%" -m pip install --no-build-isolation -e "%FW%"
if errorlevel 1 exit /b %ERRORLEVEL%
"%PY%" -m pip install --no-build-isolation -e "%ROOT%"
if errorlevel 1 exit /b %ERRORLEVEL%

set "SST_FALSIFIER_FRAMEWORK_ROOT=%FW%"
"%PY%" "%ROOT%\run_instance.py" SELFTEST
exit /b %ERRORLEVEL%
