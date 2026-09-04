@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  set "PYTHON=.venv\Scripts\python.exe"
) else (
  set "PYTHON=python"
)
echo [SST] Native preflight using "%PYTHON%"
"%PYTHON%" run_native_preflight.py
if errorlevel 1 (
  echo [SST] Native preflight failed. The QM campaign was not started.
  exit /b %errorlevel%
)
"%PYTHON%" scripts\run_qm.py --preset quick --require-native --skip-native-build --ids L2a1 L4a1 L5a1 L6a4 L6n1 L7n1 %*
exit /b %errorlevel%
