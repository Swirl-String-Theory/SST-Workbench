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

set "OUT=%ROOT%\outputs\research_campaign"
if not exist "%OUT%" mkdir "%OUT%"
echo === VOLLEDIGE research campaign ===
echo 4 resoluties x 4 epsilons x 3 kernels x 4 knopen, inclusief evoluties.
echo Dit is de zwaarste standaardrun in het pakket.
echo.
choice /M "Volledige campagne starten"
if errorlevel 2 exit /b 0

%PY_CMD% src\sst_dimensionless_ratios.py campaign --config configs\research_campaign.json --output "%OUT%"
if errorlevel 1 goto :fail

echo.
echo [OK] Volledige researchcampagne afgerond.
start "" "%OUT%"
pause
exit /b 0

:fail
echo [ERROR] Volledige researchcampagne faalde.
pause
exit /b 1
