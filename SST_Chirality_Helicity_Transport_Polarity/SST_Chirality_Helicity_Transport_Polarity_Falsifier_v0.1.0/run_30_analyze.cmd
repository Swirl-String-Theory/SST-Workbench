@echo off
setlocal
cd /d "%~dp0"
set CFG=%~1
set OUT=%~2
if "%CFG%"=="" set CFG=configs\basic.json
if "%OUT%"=="" set OUT=outputs\manual
.venv\Scripts\python.exe -m sst_chiral.analyze "%CFG%" "%OUT%" || exit /b 1
exit /b 0
