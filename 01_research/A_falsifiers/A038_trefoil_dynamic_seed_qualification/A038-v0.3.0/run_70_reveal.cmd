@echo off
setlocal
call _common.cmd
set OUT=%~1
if "%OUT%"=="" set OUT=outputs\basic
call .venv\Scripts\activate.bat
python -m sst_seed_falsifier.cli reveal "%OUT%" || exit /b 1
echo Reveal summary: %OUT%\REVEAL_SUMMARY.json
