@echo off
setlocal
call "%~dp0_common.bat"
if errorlevel 1 exit /b 1
cd /d "%ROOT%"
set PY_CMD="%ROOT%\.venv\Scripts\python.exe"
set OUT=%ROOT%\outputs\bundle_mode_analysis
if not exist "%OUT%" mkdir "%OUT%"

if not exist "%ROOT%\outputs\bundle_physical_tubes\campaign_summary.csv" (
  echo [ERROR] Ontbreekt: outputs\bundle_physical_tubes\campaign_summary.csv
  echo Voer eerst batch\21_test_physical_tubes.bat uit.
  pause
  exit /b 1
)
if not exist "%ROOT%\outputs\bundle_numerical_discretization\campaign_summary.csv" (
  echo [ERROR] Ontbreekt: outputs\bundle_numerical_discretization\campaign_summary.csv
  echo Voer eerst batch\22_test_numerical_discretization.bat uit.
  pause
  exit /b 1
)

%PY_CMD% tools\analyze_bundle_modes.py ^
  --physical-input outputs\bundle_physical_tubes ^
  --numerical-input outputs\bundle_numerical_discretization ^
  --output "%OUT%"
if errorlevel 1 goto :fail
start "" "%OUT%"
pause
exit /b 0
:fail
echo [ERROR] Analyse faalde.
pause
exit /b 1
