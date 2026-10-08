@echo off
setlocal
cd /d "%~dp0"
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo [A056] Missing .venv. Run run_install.cmd first.
  exit /b 2
)
set "INPUT=%~1"
if "%INPUT%"=="" set "INPUT=data\runtime_e010_filament"
"%PY%" -m tools.diagnose_g2 --input-dir "%INPUT%" --config configs\e010_real_score.json --json-out A056_G2_DIAGNOSTICS_READONLY.json
exit /b %ERRORLEVEL%
