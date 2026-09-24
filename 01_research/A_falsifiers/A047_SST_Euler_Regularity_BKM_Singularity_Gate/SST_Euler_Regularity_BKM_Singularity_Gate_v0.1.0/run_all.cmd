@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo SST Euler Regularity / BKM Singularity Gate v0.1.0
echo A043 - BASIC blind dimensionless campaign
echo ============================================================
if not exist .venv py -3 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip setuptools wheel pybind11 numpy pytest || exit /b 1
python -m pip install -e . || exit /b 1
python -m pytest -q || exit /b 1
python -m sst_bkm.campaign --config config\basic.json || exit /b 1
python tools_make_manifest.py || exit /b 1
echo Complete.
