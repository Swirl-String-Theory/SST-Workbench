@echo off
setlocal
call _common.cmd
set DATA=%~1
if "%DATA%"=="" set DATA=..\..\KnotPlot\knots\final
set OUT=%~2
if "%OUT%"=="" set OUT=outputs\basic
set CFG=%~3
if "%CFG%"=="" set CFG=config\basic.json
call .venv\Scripts\activate.bat
if exist "%OUT%" rmdir /s /q "%OUT%"
python -m sst_seed_falsifier.cli prepare "%DATA%" "%OUT%" "%CFG%" || exit /b 1
