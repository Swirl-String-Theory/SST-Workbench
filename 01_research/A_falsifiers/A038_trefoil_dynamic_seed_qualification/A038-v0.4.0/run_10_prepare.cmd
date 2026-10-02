@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
set DATA=%~1
set OUT=%~2
set CFG=%~3
if "%DATA%"=="" exit /b 2
if "%OUT%"=="" set OUT=SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier_v0.3.3-outputs\basic
if "%CFG%"=="" set CFG=config\basic.json
"%PY%" -m sst_seed_falsifier.cli prepare "%DATA%" "%OUT%" "%CFG%"
