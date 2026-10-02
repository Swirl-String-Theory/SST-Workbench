@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (echo [SST] .venv missing. Run run_install.cmd first.& exit /b 1)
echo ============================================================
echo [SST] Building optimized C++/pybind11 backend
echo ============================================================
".venv\Scripts\python.exe" setup.py build_ext --inplace
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -m einstein_sst_gates.cli cpp-info
if errorlevel 1 exit /b 1
