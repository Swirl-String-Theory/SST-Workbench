@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "FW=%~dp0..\..\..\..\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.6"
if defined SST_FALSIFIER_FRAMEWORK_ROOT set "FW=%SST_FALSIFIER_FRAMEWORK_ROOT%"

if not exist "%FW%\sst_falsifier\__init__.py" (
  echo [ERROR] SST Falsifier Framework v1.0.6 not found:
  echo         %FW%
  echo Set SST_FALSIFIER_FRAMEWORK_ROOT to the canonical v1.0.6 directory.
  exit /b 4
)

if not exist "%FW%\.venv\Scripts\python.exe" (
  echo [A016] Framework environment absent; running v1.0.6 setup...
  call "%FW%\run_00_setup.cmd"
  if errorlevel 1 exit /b %ERRORLEVEL%
)
set "PY=%FW%\.venv\Scripts\python.exe"
set "SST_FALSIFIER_FRAMEWORK_ROOT=%FW%"

if "%~1"=="" (set "MODE=FULL") else (set "MODE=%~1")

if /I "%MODE%"=="SETUP" (
  call "%FW%\run_00_setup.cmd"
  exit /b %ERRORLEVEL%
)
if /I "%MODE%"=="SELFTEST" (
  "%PY%" -m pytest -q
  exit /b %ERRORLEVEL%
)
if /I "%MODE%"=="FREEZE" goto RUNMODE
if /I "%MODE%"=="BASIC" goto ENSURE_FREEZE
if /I "%MODE%"=="FULL" goto ENSURE_FREEZE
if /I "%MODE%"=="CERTIFY" goto ENSURE_FREEZE
if /I "%MODE%"=="REVEAL" goto ENSURE_FREEZE

echo Usage: run_all.cmd [SETUP^|SELFTEST^|FREEZE^|BASIC^|FULL^|CERTIFY^|REVEAL]
exit /b 2

:ENSURE_FREEZE
if not exist "preregistration\FROZEN_PROTOCOL.json" (
  echo [A016] No frozen protocol found; freezing v0.2.2 before %MODE%...
  "%PY%" run_instance.py FREEZE
  if errorlevel 1 exit /b %ERRORLEVEL%
)

if /I "%MODE%"=="BASIC" goto E011_PREFLIGHT
if /I "%MODE%"=="FULL" goto E011_PREFLIGHT
if /I "%MODE%"=="CERTIFY" goto E011_PREFLIGHT
goto RUNMODE

:E011_PREFLIGHT
"%PY%" tools\preflight_e011.py %MODE%
if errorlevel 1 exit /b %ERRORLEVEL%
goto RUNMODE

:RUNMODE
"%PY%" run_instance.py %MODE%
exit /b %ERRORLEVEL%
