@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
set OUT=%~1
if "%OUT%"=="" set OUT=SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier_v0.3.3-outputs\basic
"%PY%" -m sst_seed_falsifier.cli reveal "%OUT%"
