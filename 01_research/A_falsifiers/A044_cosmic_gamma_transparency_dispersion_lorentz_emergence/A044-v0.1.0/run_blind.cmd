\
@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo [ERROR] .venv missing. Run run_all.cmd first.
  exit /b 2
)
"%PY%" -m sst_cgtdlef.run blind --config configs\blind_config.json
if errorlevel 1 exit /b %errorlevel%
"%PY%" tools\verify_blind_clean.py --root .
exit /b %errorlevel%
