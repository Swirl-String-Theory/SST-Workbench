@echo off
setlocal
call "%~dp0_common.cmd" || exit /b 1
pushd "%~dp0"

echo.
echo ============================================================
echo [1_MaxwellSST] Install / update v0.2.0
echo ============================================================
"%PYTHON_EXE%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 echo [WARN] pip/setuptools/wheel upgrade failed; continuing with installed versions.
"%PYTHON_EXE%" -m pip install -e ".[dev]" --no-build-isolation
if errorlevel 1 goto :fail

echo.
echo [1_MaxwellSST] Installing optional native dependency pybind11...
"%PYTHON_EXE%" -m pip install "pybind11>=2.13"
if errorlevel 1 (
  echo [WARN] pybind11 install failed. Python fallback remains usable.
)

echo.
echo [1_MaxwellSST] Building C++17 pybind backend when possible...
"%PYTHON_EXE%" -m maxwell_sst_falsifier.native_ext.build_ext_if_needed --force
"%PYTHON_EXE%" -m maxwell_sst_falsifier backend

echo.
echo [1_MaxwellSST] Running tests...
"%PYTHON_EXE%" -m pytest -q
if errorlevel 1 goto :fail

echo.
echo [OK] Installation complete.
popd
exit /b 0
:fail
echo [ERROR] Installation/check failed with code %errorlevel%.
popd
exit /b 1
