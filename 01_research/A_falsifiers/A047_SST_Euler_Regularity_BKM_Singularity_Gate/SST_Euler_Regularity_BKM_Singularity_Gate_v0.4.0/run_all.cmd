@echo off
setlocal
cd /d "%~dp0"
set WB=%~1
set CFG=%~2
set PARENT=%~3
if "%WB%"=="" set WB=%SST_WORKBENCH_ROOT%
if "%WB%"=="" set WB=C:\workspace\projects\SST-Workbench
if "%CFG%"=="" set CFG=config\v040_basic.json
echo ============================================================
echo A047 SST Euler Regularity / BKM Gate v0.4.0
echo Resolution-certified Lagrangian follow-up
echo Workbench: %WB%
echo Config: %CFG%
echo ============================================================
call run_00_setup.cmd || exit /b 1
call run_stage.cmd all "%WB%" "%CFG%" "%PARENT%" || exit /b 1
call .venv\Scripts\activate.bat
python tools_make_manifest.py || exit /b 1
echo A047 v0.4.0 complete.
