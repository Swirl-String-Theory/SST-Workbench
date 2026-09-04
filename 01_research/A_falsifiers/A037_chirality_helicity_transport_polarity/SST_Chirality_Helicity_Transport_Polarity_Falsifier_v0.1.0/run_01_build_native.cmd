@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo Build native C++17 / pybind11 / OpenMP backend
echo ============================================================
if not exist .venv\Scripts\python.exe (
  call run_00_setup.cmd
  if errorlevel 1 exit /b 1
)
.venv\Scripts\python.exe setup.py build_ext --inplace
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -c "import native_ext; print('[native] OK:', native_ext.__file__)"
if errorlevel 1 exit /b 1
exit /b 0
