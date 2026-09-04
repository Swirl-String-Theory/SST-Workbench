@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo Build C++17 / pybind11 / OpenMP multi-component backend
echo ============================================================
if not exist .venv\Scripts\python.exe call run_00_setup.cmd || exit /b 1
.venv\Scripts\python.exe setup.py build_ext --inplace || exit /b 1
.venv\Scripts\python.exe -c "import native_ext; print('[native] OK:', native_ext.__file__)" || exit /b 1
exit /b 0
