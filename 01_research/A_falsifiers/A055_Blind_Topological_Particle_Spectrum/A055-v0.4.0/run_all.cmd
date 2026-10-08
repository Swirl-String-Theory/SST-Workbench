@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "MODE=%~1"
if "%MODE%"=="" set "MODE=full"
set "WB=%~2"
if "%WB%"=="" set "WB=C:\workspace\projects\SST-Workbench"
set "SST_WORKBENCH_ROOT=%WB%"
call run_install.cmd || exit /b 1
call run_10_selftest.cmd || exit /b 1
set "PY=.venv\Scripts\python.exe"
%PY% run_instance.py FREEZE || exit /b 1
if /I "%MODE%"=="basic" (
  %PY% run_instance.py BASIC || exit /b 1
  exit /b 0
)
if /I "%MODE%"=="full" (
  %PY% run_instance.py FULL || exit /b 1
  %PY% run_instance.py REVEAL || exit /b 1
  %PY% tools\package_outputs.py || exit /b 1
  exit /b 0
)
if /I "%MODE%"=="certify" (
  %PY% run_instance.py CERTIFY || exit /b 1
  %PY% run_instance.py REVEAL || exit /b 1
  %PY% tools\package_outputs.py || exit /b 1
  exit /b 0
)
echo Usage: run_all.cmd [basic^|full^|certify] [SST-Workbench-root]
exit /b 2
