@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "WB=%~1"
if "%WB%"=="" set "WB=C:\workspace\projects\SST-Workbench"
set "E010=%~2"
set "PY=.venv\Scripts\python.exe"

echo [1/5] Python environment
if not exist "%PY%" (
  where py >nul 2>nul && (py -3 -m venv .venv) || (python -m venv .venv)
  if errorlevel 1 exit /b 1
)
"%PY%" -m pip install --disable-pip-version-check -q -r requirements.txt
if errorlevel 1 exit /b 1

echo [2/5] Tests
"%PY%" -m pytest -q tests
if errorlevel 1 exit /b 1

echo [3/5] E010-v0.3.1 parent + selected topology admission/analysis
if "%E010%"=="" (
  "%PY%" tools\run_analysis.py --workbench-root "%WB%" --mode selected
) else (
  "%PY%" tools\run_analysis.py --workbench-root "%WB%" --e010-output "%E010%" --mode selected
)
if errorlevel 1 exit /b 1

echo [4/5] Pack outputs
"%PY%" tools\pack_outputs.py
if errorlevel 1 exit /b 1

echo [5/5] Complete
echo Outputs: %CD%\E011_SKLSA_Selected_Qualified_Carrier_Analysis_v0.2.0-outputs
echo ZIP:     %CD%\..\E011_SKLSA_Selected_Qualified_Carrier_Analysis_v0.2.0-outputs.zip
exit /b 0
