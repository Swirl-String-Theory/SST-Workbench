@echo off
setlocal
set "ROOT=%~dp0"
cd /d "%ROOT%"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "OMP_NUM_THREADS=16"
set "OPENBLAS_NUM_THREADS=1"
set "MKL_NUM_THREADS=1"
if not exist ".venv\Scripts\python.exe" (
  echo [FC-PHASE] Missing .venv. Run run_00_install.cmd first.
  exit /b 1
)
set "PY=.venv\Scripts\python.exe"
endlocal & set "ROOT=%ROOT%" & set "PY=%PY%" & set "PYTHONUTF8=1" & set "PYTHONIOENCODING=utf-8" & set "OMP_NUM_THREADS=16" & set "OPENBLAS_NUM_THREADS=1" & set "MKL_NUM_THREADS=1"
