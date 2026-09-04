@echo off
setlocal
call _common.cmd
set OUT=%~1
if "%OUT%"=="" set OUT=outputs\basic
set CFG=%~2
if "%CFG%"=="" set CFG=config\basic.json
call .venv\Scripts\activate.bat
python -m sst_seed_falsifier.cli early "%OUT%" "%CFG%" || exit /b 1
