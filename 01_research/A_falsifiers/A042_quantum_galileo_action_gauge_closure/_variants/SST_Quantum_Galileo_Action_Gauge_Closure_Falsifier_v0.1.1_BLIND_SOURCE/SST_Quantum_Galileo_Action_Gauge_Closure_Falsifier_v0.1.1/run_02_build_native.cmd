@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo [2/7] Build C++17 / pybind11 native backend
echo ============================================================
call .venv\Scripts\activate.bat

python setup.py build_ext --inplace
if errorlevel 1 (
  echo.
  echo ERROR: native build failed.
  echo Review the compiler/build output ABOVE for the actual cause.
  echo Common categories:
  echo   - setuptools package discovery/configuration
  echo   - C++ source portability/compiler errors
  echo   - missing or incompatible Visual C++ build tools
  echo   - pybind11/Python ABI configuration
  echo.
  exit /b 1
)

python -c "import sst_qgi_native; print('native backend: cpp-pybind11')"
if errorlevel 1 (
  echo ERROR: native extension was built but could not be imported.
  exit /b 1
)
endlocal
