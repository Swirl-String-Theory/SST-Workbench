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

set "OUT=%ROOT%\outputs\medium_campaign"
if not exist "%OUT%" mkdir "%OUT%"
echo === Medium convergence campaign ===
echo 2 resoluties x 2 epsilons x 3 kernels x 4 knopen.
%PY_CMD% src\sst_dimensionless_ratios.py campaign --config configs\medium_campaign.json --output "%OUT%"
if errorlevel 1 goto :fail

echo.
echo [OK] Medium-campagne afgerond.
start "" "%OUT%"
pause
exit /b 0

:fail
echo [ERROR] Medium-campagne faalde.
pause
exit /b 1
