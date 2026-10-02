@echo off
setlocal
call _common.cmd
set OUT=%~1
if "%OUT%"=="" set OUT=SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier_v0.3.1-outputs\basic
call .venv\Scripts\activate.bat
python -m sst_seed_falsifier.cli reveal "%OUT%" || exit /b 1
echo Reveal summary: %OUT%\REVEAL_SUMMARY.json
