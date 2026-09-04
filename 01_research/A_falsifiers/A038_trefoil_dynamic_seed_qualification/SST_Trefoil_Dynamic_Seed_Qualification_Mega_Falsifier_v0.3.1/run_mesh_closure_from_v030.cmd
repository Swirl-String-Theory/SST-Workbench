@echo off
setlocal EnableExtensions
call _common.cmd
set SOURCE=%~1
if "%SOURCE%"=="" (
  echo Usage: run_mesh_closure_from_v030.cmd ^<v0.3.0 scientific_campaign directory^> [config]
  exit /b 2
)
set CFG=%~2
if "%CFG%"=="" set CFG=config\prospective_atlas.json
set ROOTOUT=SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier_v0.3.1-outputs
set DEST=%ROOTOUT%\posthoc_v030_mesh_closure
call run_00_setup.cmd || exit /b 1
call run_01_build_native.cmd || exit /b 1
call .venv\Scripts\activate.bat
python -m sst_seed_falsifier.posthoc "%SOURCE%" "%DEST%" "%CFG%" || exit /b 1
python -m sst_seed_falsifier.archive blind "%ROOTOUT%" || exit /b 1
echo ============================================================
echo POST-HOC S37B diagnostic complete.
echo This does NOT certify S37A and cannot promote to S40.
echo Inspect: %DEST%\summary.json
echo ============================================================
