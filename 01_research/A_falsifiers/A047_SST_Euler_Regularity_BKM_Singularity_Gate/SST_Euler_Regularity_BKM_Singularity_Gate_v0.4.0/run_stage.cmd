@echo off
setlocal
cd /d "%~dp0"
set STAGE=%~1
set WB=%~2
set CFG=%~3
set PARENT=%~4
if "%STAGE%"=="" set STAGE=all
if "%WB%"=="" set WB=%SST_WORKBENCH_ROOT%
if "%WB%"=="" set WB=C:\workspace\projects\SST-Workbench
if "%CFG%"=="" set CFG=config\v040_basic.json
if not exist .venv call run_00_setup.cmd || exit /b 1
call .venv\Scripts\activate.bat || exit /b 1
set PARG=
if not "%PARENT%"=="" set PARG=--parent-v030-output "%PARENT%"
python -m sst_bkm.campaign --stage "%STAGE%" --config "%CFG%" --workbench-root "%WB%" %PARG% || exit /b 1
