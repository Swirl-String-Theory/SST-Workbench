@echo off
call "%~dp0_common.cmd" || exit /b 1
cd /d "%ROOT%"
echo [FC-PHASE] Building C++17/OpenMP pybind11 helper...
"%PY%" setup_native.py build_ext --inplace
if errorlevel 1 exit /b 1
"%PY%" -m sst_finite_core_falsifier.cli backend
if errorlevel 1 exit /b 1
