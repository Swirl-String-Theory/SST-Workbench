@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
set OUT=%~1
set CFG=%~2
if "%OUT%"=="" set OUT=SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier_v0.3.3-outputs
if "%CFG%"=="" set CFG=config\basic.json
"%PY%" -m sst_seed_falsifier.cli temporal "%OUT%" "%CFG%"
