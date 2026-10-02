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
if errorlevel 1 exit /b %errorlevel%
"%PYTHON%" scripts\run_continuum.py --config configs\qm_full.json --output outputs_continuum_full --require-native --skip-native-build %*
exit /b %errorlevel%
