@echo off
setlocal
cd /d "%~dp0"
for %%I in ("%CD%\..\..\..\..") do set "SST_WORKBENCH_ROOT=%%~fI"
set "SST_FALSIFIER_FRAMEWORK_ROOT=%SST_WORKBENCH_ROOT%\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.7"
set "PYTHONPATH=%CD%;%PYTHONPATH%"
if not exist .venv\Scripts\python.exe (
  where py >nul 2>&1
  if not errorlevel 1 (py -3 -m venv .venv) else (python -m venv .venv)
  if errorlevel 1 exit /b 1
)
set "PY=.venv\Scripts\python.exe"
"%PY%" -m pip install -q -r requirements.txt
if errorlevel 1 exit /b 1
if /I "%~1"=="SELFTEST" (
  "%PY%" -m pytest tests -q
  exit /b %ERRORLEVEL%
)
if /I "%~1"=="FREEZE" (
  "%PY%" run_instance.py FREEZE
  exit /b %ERRORLEVEL%
)
if /I "%~1"=="REVEAL" (
  "%PY%" run_instance.py REVEAL_IF_ALLOWED
  exit /b %ERRORLEVEL%
)
if not exist preregistration\FROZEN_PROTOCOL.json (
  "%PY%" run_instance.py FREEZE
  if errorlevel 1 exit /b 1
)
set "MODE=FULL"
if /I "%~1"=="BASIC" set "MODE=BASIC"
if /I "%~1"=="CERTIFY" set "MODE=CERTIFY"
"%PY%" run_instance.py %MODE%
set "EXITCODE=%ERRORLEVEL%"
"%PY%" tools\ensure_pdf.py
if not "%EXITCODE%"=="0" exit /b %EXITCODE%
exit /b 0
