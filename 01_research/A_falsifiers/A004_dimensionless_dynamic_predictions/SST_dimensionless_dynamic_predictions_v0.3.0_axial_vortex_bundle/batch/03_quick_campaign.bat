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

set "OUT=%ROOT%\outputs\quick_batch"
if not exist "%OUT%" mkdir "%OUT%"
echo === Quick campaign: ring, trefoil, spiegel-trefoil, figure-eight ===
%PY_CMD% src\sst_dimensionless_ratios.py campaign --config configs\quick_campaign.json --output "%OUT%"
if errorlevel 1 goto :fail

echo.
echo [OK] Uitvoer staat in:
echo %OUT%
echo.
start "" "%OUT%"
pause
exit /b 0

:fail
echo [ERROR] Quick campaign faalde.
pause
exit /b 1
