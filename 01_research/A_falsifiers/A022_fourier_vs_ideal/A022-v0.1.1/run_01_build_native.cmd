@echo off
setlocal
cd /d "%~dp0"
call _common.cmd || exit /b 1
echo [SST-FVI] Building C++17/pybind11 native backend...
"%PY%" setup_native.py build_ext --inplace
if errorlevel 1 (
  echo [SST-FVI] Native build failed. Basic torus run may use NumPy fallback; extended run requires native.
  exit /b 1
)
"%PY%" -m sst_fourier_ideal_falsifier.cli backend
exit /b %errorlevel%
