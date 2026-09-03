@echo off
setlocal
call _common.cmd
set OUT=%~1
if "%OUT%"=="" set OUT=SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier_v0.3.1-outputs\basic
set CFG=%~2
if "%CFG%"=="" set CFG=config\basic.json
call .venv\Scripts\activate.bat
python -m sst_seed_falsifier.cli mechanism "%OUT%" "%CFG%" || exit /b 1
