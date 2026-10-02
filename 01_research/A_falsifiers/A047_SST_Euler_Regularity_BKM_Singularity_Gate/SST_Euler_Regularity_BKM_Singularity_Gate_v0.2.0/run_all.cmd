@echo off
setlocal
cd /d "%~dp0"
set PKLSA=%~1
if "%PKLSA%"=="" set PKLSA=%SST_PKLSA_ROOT%
if "%PKLSA%"=="" (
  echo ERROR: PKLSA root required.
  echo Usage: run_all.cmd "C:\path\to\SST_Parametric_Knot_Link_Seed_Atlas_v0.1.1"
  echo Or set SST_PKLSA_ROOT.
  exit /b 2
)
set CFG=%~2
if "%CFG%"=="" set CFG=config\pklsa_basic.json
echo ============================================================
echo SST Euler Regularity / BKM Singularity Gate v0.2.0
echo A043 - PKLSA trefoil population blind campaign
echo PKLSA: %PKLSA%
echo Config: %CFG%
echo ============================================================
if not exist .venv py -3 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip setuptools wheel pybind11 numpy pytest || exit /b 1
python -m pip install -e . || exit /b 1
python -m pytest -q || exit /b 1
python -m sst_bkm.campaign --config "%CFG%" --pklsa-root "%PKLSA%" || exit /b 1
python tools_make_manifest.py || exit /b 1
echo Complete.
