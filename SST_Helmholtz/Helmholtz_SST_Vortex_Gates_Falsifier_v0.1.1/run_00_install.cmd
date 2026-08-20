@echo off
setlocal EnableExtensions
call "%~dp0_paths.cmd"
cd /d "%ROOT%"
echo [H-SST] Root: %ROOT%
echo [H-SST] Knots: %SST_KNOTS_DIR%
if not exist "%VENV%\Scripts\python.exe" (
  where py >nul 2>nul && (py -3.14 -m venv "%VENV%" 2>nul || py -3 -m venv "%VENV%")
  if not exist "%VENV%\Scripts\python.exe" python -m venv "%VENV%"
)
if not exist "%VENV%\Scripts\python.exe" (echo [ERROR] Could not create venv.& exit /b 1)
"%PY%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 exit /b %errorlevel%
"%PY%" -m pip install -r requirements.txt
if errorlevel 1 exit /b %errorlevel%
echo [H-SST] Building C++17 pybind11 backend...
"%PY%" -m native_ext.build_ext_if_needed --force --strict
if errorlevel 1 (
  echo [ERROR] Native C++ build failed. If cl.exe appears in the compile log above, Visual Studio Build Tools are already installed; inspect the compiler error instead.
  exit /b 1
)
"%PY%" run_native_parity.py --threads %SST_NATIVE_THREADS% --require-native
if errorlevel 1 exit /b %errorlevel%
echo [H-SST] INSTALL PASS
exit /b 0
