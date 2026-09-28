@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "WB=%~1"
if "%WB%"=="" set "WB=C:\workspace\projects\SST-Workbench"
set "E010=%~2"
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (
  where py >nul 2>nul && (py -3 -m venv .venv) || (python -m venv .venv)
  if errorlevel 1 exit /b 1
)
"%PY%" -m pip install --disable-pip-version-check -q -r requirements.txt
if errorlevel 1 exit /b 1
if "%E010%"=="" (
  "%PY%" tools\run_analysis.py --workbench-root "%WB%" --mode poc --output-root E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs-POC
) else (
  "%PY%" tools\run_analysis.py --workbench-root "%WB%" --e010-output "%E010%" --mode poc --output-root E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs-POC
)
exit /b %ERRORLEVEL%
