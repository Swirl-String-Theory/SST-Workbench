@echo off
setlocal
cd /d "%~dp0.."
if defined SST_PYTHON (set "PY=%SST_PYTHON%") else if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=python")
"%PY%" -c "from framework_bootstrap import load_framework; load_framework(); from sst_falsifier.native_build import build_pybind; from pathlib import Path; import sys; result=build_pybind(Path.cwd(), prefer_openmp=True, force=True); print(result); sys.exit(0 if result.success else 2)"
exit /b %ERRORLEVEL%
