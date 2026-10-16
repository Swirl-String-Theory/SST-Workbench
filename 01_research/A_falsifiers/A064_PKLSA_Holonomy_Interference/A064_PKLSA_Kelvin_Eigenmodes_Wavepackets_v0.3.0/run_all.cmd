@echo off
setlocal
cd /d "%~dp0"
set OPENBLAS_NUM_THREADS=1
set OMP_NUM_THREADS=1
set MKL_NUM_THREADS=1
set NUMEXPR_NUM_THREADS=1
if not exist .venv\Scripts\python.exe (
  py -3 -m venv .venv || exit /b 1
)
.venv\Scripts\python.exe -m pip install -r requirements.txt || exit /b 1
.venv\Scripts\python.exe -m pytest -q tests || exit /b 1
set A064_PHASE=PRIMARY
.venv\Scripts\python.exe src\run_kelvin.py || exit /b 1
set A064_PHASE=CONTROLS
.venv\Scripts\python.exe src\run_kelvin.py || exit /b 1
.venv\Scripts\python.exe src\render_report.py || exit /b 1
.venv\Scripts\python.exe src\package.py || exit /b 1
endlocal
