@echo off
setlocal
cd /d "%~dp0"
set WB=%~1
if "%WB%"=="" set WB=%SST_WORKBENCH_ROOT%
if "%WB%"=="" set WB=C:\workspace\projects\SST-Workbench
set CFG=%~2
if "%CFG%"=="" set CFG=config\e010_v031_basic.json

echo ============================================================
echo SST Euler Regularity / BKM Singularity Gate v0.3.0
echo A047 - E010 PKLSA v0.3.1 source-native trefoil campaign
echo Workbench: %WB%
echo Config: %CFG%
echo ============================================================

if not exist .venv py -3 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip setuptools wheel pybind11 numpy pytest || exit /b 1
python -m pip install -e . || exit /b 1
python -m pytest -q || exit /b 1
python -m sst_bkm.campaign --config "%CFG%" --workbench-root "%WB%" || exit /b 1
python tools_make_manifest.py || exit /b 1

echo ============================================================
echo A047 v0.3.0 complete.
echo ============================================================
