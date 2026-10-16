@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "MODE=%~1"
if "%MODE%"=="" set "MODE=BASIC"
set "WB=%~2"
if not "%WB%"=="" set "SST_WORKBENCH_ROOT=%WB%"
if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=python")
set "PYTHONPATH=%CD%;%PYTHONPATH%"
if /I "%MODE%"=="BASIC" goto budget
if "%MODE%"=="512" goto budget
if "%MODE%"=="2048" goto budget
if "%MODE%"=="32768" goto budget
"%PY%" run_instance.py %MODE%
exit /b %ERRORLEVEL%
:budget
"%PY%" tools\run_budget.py %MODE%
exit /b %ERRORLEVEL%
