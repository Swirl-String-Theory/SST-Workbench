@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "SRC=%~1"
set "WB=%~2"
if "%SRC%"=="" set "SRC=..\A058-v0.1.3"
if "%WB%"=="" (
  if not "%SST_WORKBENCH%"=="" set "WB=%SST_WORKBENCH%"
)
if "%WB%"=="" (
  if not "%SST_WORKBENCH_ROOT%"=="" set "WB=%SST_WORKBENCH_ROOT%"
)
call run_install.cmd || exit /b 1
.venv\Scripts\python.exe tools\check_private_material.py || exit /b 1
call run_python.cmd tools\import_v013_campaign.py --source "%SRC%" || exit /b 1
call run_all.cmd SELFTEST "%WB%" || exit /b 1
call run_all.cmd FREEZE "%WB%" || exit /b 1
call run_all.cmd FULL "%WB%"
exit /b %ERRORLEVEL%
