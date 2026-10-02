@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call _common.cmd
if errorlevel 1 exit /b 1
echo [SST-TH] Building C++17/pybind11 backend...
"%PY%" setup_native.py build_ext --inplace
if errorlevel 1 exit /b 1
"%PY%" -m sst_threaded_hole_falsifier.cli backend
exit /b %errorlevel%
