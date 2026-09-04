@echo off
setlocal
call _common.cmd
set DATA=%~1
if "%DATA%"=="" (
  echo Dataset path required. Scientific profiles require a fresh held-out atlas.
  exit /b 2
)
set OUT=%~2
if "%OUT%"=="" set OUT=SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier_v0.3.1-outputs\basic
set CFG=%~3
if "%CFG%"=="" set CFG=config\basic.json
call .venv\Scripts\activate.bat
if exist "%OUT%" (
  echo Refusing to overwrite existing evidence directory: %OUT%
  echo Choose a fresh output path or archive the existing run first.
  exit /b 2
)
if exist "%OUT%_sealed_private" (
  echo Refusing to overwrite existing sealed private bundle: %OUT%_sealed_private
  exit /b 2
)
python -m sst_seed_falsifier.cli prepare "%DATA%" "%OUT%" "%CFG%" || exit /b 1
