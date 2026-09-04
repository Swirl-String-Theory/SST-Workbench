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

echo === Interne ring sanity check ===
%PY_CMD% src\sst_dimensionless_ratios.py selftest
if errorlevel 1 goto :fail

echo.
echo [PASS] De ringnormalisatie, energie, reach en relative-equilibrium-residu zijn geldig.
pause
exit /b 0

:fail
echo.
echo [FAIL] De selftest faalde. Gebruik de uitvoer hierboven voor diagnose.
pause
exit /b 1
