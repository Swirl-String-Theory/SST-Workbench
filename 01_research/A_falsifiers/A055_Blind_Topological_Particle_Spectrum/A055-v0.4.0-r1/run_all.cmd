@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "MODE=%~1"
if "%MODE%"=="" set "MODE=full"
set "WB=%~2"
if "%WB%"=="" set "WB=C:\workspace\projects\SST-Workbench"
set "SST_WORKBENCH_ROOT=%WB%"
set "PY=.venv\Scripts\python.exe"

call run_install.cmd
if errorlevel 1 goto :fail

call run_10_selftest.cmd
if errorlevel 1 goto :fail

"%PY%" run_instance.py FREEZE
if errorlevel 1 goto :fail

if /I "%MODE%"=="basic" goto :basic
if /I "%MODE%"=="full" goto :full
if /I "%MODE%"=="certify" goto :certify

echo Usage: run_all.cmd [basic^|full^|certify] [SST-Workbench-root]
exit /b 2

:basic
"%PY%" run_instance.py BASIC
if errorlevel 1 goto :fail
exit /b 0

:full
"%PY%" run_instance.py FULL
if errorlevel 1 goto :fail
"%PY%" run_instance.py REVEAL
if errorlevel 1 goto :fail
"%PY%" tools\package_outputs.py
if errorlevel 1 goto :fail
exit /b 0

:certify
"%PY%" run_instance.py CERTIFY
if errorlevel 1 goto :fail
"%PY%" run_instance.py REVEAL
if errorlevel 1 goto :fail
"%PY%" tools\package_outputs.py
if errorlevel 1 goto :fail
exit /b 0

:fail
set "RC=%ERRORLEVEL%"
if "%RC%"=="0" set "RC=1"
echo.
echo A055 run failed with exit code %RC%.
exit /b %RC%
