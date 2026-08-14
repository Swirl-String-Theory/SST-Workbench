@echo off
setlocal EnableExtensions
call "%~dp0_paths.cmd"
cd /d "%ROOT%"
echo [DFC] Root: %ROOT%
echo [DFC] Knots: %SST_KNOTS_DIR%
if not exist "%VENV%\Scripts\python.exe" (
  where py >nul 2>nul && (py -3.14 -m venv "%VENV%" 2>nul || py -3 -m venv "%VENV%")
  if not exist "%VENV%\Scripts\python.exe" python -m venv "%VENV%"
)
if not exist "%VENV%\Scripts\python.exe" (echo [ERROR] Could not create venv.& exit /b 1)
"%PY%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 exit /b %errorlevel%
"%PY%" -m pip install -r requirements.txt
if errorlevel 1 exit /b %errorlevel%
echo [DFC] Building native pybind11 extension...
"%PY%" -m native_ext.build_ext_if_needed --force --strict
if errorlevel 1 (
 echo [ERROR] Native build failed. Install Visual Studio Build Tools with Desktop development with C++ and rerun.
 exit /b 1
)
if exist "%SST_KNOTS_DIR%\knot_3.1_final.txt" (
 "%PY%" run_native_parity.py --knots-dir "%SST_KNOTS_DIR%" --require-native --threads %SST_NATIVE_THREADS%
 if errorlevel 1 exit /b %errorlevel%
) else (
 echo [WARN] Knot directory not found yet; native build succeeded but geometry parity was skipped.
)
echo [DFC] INSTALL PASS
exit /b 0
