@echo off
setlocal
call "%~dp0_common.bat"
if errorlevel 1 exit /b 1
cd /d "%ROOT%"
if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] Voer eerst batch\01_setup_venv.bat uit.
  pause
  exit /b 1
)
set "CSV=%ROOT%\outputs\infinite_background_vortex_quick\campaign_summary.csv"
set "REPORT=%ROOT%\outputs\infinite_background_vortex_quick\background_invariance_report.json"
if not exist "%CSV%" (
  echo [ERROR] Start eerst batch\10_infinite_background_vortex_quick.bat
  pause
  exit /b 1
)
%PY_CMD% tools\analyze_background_invariance.py "%CSV%" --output "%REPORT%"
if errorlevel 1 goto :fail
echo.
echo [PASS] Intrinsieke residual is invariant onder solid-body achtergrondrotatie.
start "" "%REPORT%"
pause
exit /b 0
:fail
echo [FAIL] Invariantiegate faalde.
pause
exit /b 1
