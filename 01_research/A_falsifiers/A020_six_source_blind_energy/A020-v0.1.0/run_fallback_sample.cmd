@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  where py >nul 2>&1
  if not errorlevel 1 (py -3 -m venv .venv) else (python -m venv .venv)
)
set "PY=.venv\Scripts\python.exe"
"%PY%" -m pip install --upgrade pip >nul
"%PY%" -m pip install numpy >nul
"%PY%" run_campaign.py --config config\campaign_fallback_smoke.json --dataset data\sample_knots --force-python
exit /b %errorlevel%
