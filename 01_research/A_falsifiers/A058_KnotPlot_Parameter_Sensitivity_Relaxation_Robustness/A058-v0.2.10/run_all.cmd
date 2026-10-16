@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "MODE=%~1"
if "%MODE%"=="" set "MODE=BASIC"
set "WB=%~2"
if /I not "%MODE%"=="IMPORT_BASIC" if not "%WB%"=="" set "SST_WORKBENCH_ROOT=%WB%"
if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=python")
set "PYTHONPATH=%CD%;%PYTHONPATH%"
if /I "%MODE%"=="IMPORT_BASIC" goto import_legacy
if /I "%MODE%"=="BASIC" goto budget
if "%MODE%"=="512" goto budget
if "%MODE%"=="2048" goto budget
if "%MODE%"=="32768" goto budget
"%PY%" run_instance.py %MODE%
exit /b %ERRORLEVEL%
:budget
if not exist ".venv\Scripts\python.exe" (
  call "%~dp0run_install.cmd"
  if errorlevel 1 exit /b 1
  set "PY=.venv\Scripts\python.exe"
)
"%PY%" tools\run_budget.py %MODE%
exit /b %ERRORLEVEL%

:import_legacy
if "%~2"=="" (echo Usage: run_all.cmd IMPORT_BASIC "C:\path\to\A058-v0.2.9" & exit /b 2)
if not exist ".venv\Scripts\python.exe" (
  call "%~dp0run_install.cmd"
  if errorlevel 1 exit /b 1
  set "PY=.venv\Scripts\python.exe"
)
"%PY%" tools\import_prior_basic.py "%~2"
exit /b %ERRORLEVEL%
