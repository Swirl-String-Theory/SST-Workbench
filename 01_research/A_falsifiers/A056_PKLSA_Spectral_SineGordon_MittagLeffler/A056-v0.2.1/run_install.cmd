@echo off
setlocal
cd /d "%~dp0"
if not exist .venv (py -3 -m venv .venv 2>nul || python -m venv .venv) || exit /b 1
set "PY=.venv\Scripts\python.exe"
"%PY%" -m pip install --upgrade pip setuptools wheel || exit /b 1
"%PY%" -m pip install -r requirements.txt || exit /b 1
set "SST_NO_OPENMP=0"
"%PY%" setup.py build_ext --inplace --build-temp build\t --build-lib build\l
if errorlevel 1 (
  echo OpenMP/native build failed; retrying optimized serial C++...
  set "SST_NO_OPENMP=1"
  "%PY%" setup.py build_ext --inplace --force --build-temp build\t --build-lib build\l || exit /b 1
)
"%PY%" tools\capture_build_provenance.py || exit /b 1
exit /b 0
