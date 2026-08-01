@echo off
setlocal EnableExtensions
call "%~dp0_common.bat"
if errorlevel 1 exit /b 1
cd /d "%ROOT%"
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Voer eerst batch\01_setup_venv.bat uit.
    pause
    exit /b 1
)

set "OUT=%ROOT%\outputs\static_diagnostics"
if not exist "%OUT%" mkdir "%OUT%"
set "COMMON=--ideal-file data\ideal_favorites.txt --resolution 128 --epsilon 0.08 --kernel rosenhead --normalization fixed_length"

echo === 0_1 ring ===
%PY_CMD% src\sst_dimensionless_ratios.py diagnose --knot-id 0:1:1 --label ring %COMMON% --output "%OUT%\ring.json"
if errorlevel 1 goto :fail

echo === 3_1 trefoil ===
%PY_CMD% src\sst_dimensionless_ratios.py diagnose --knot-id 3:1:1 --label trefoil %COMMON% --output "%OUT%\trefoil.json"
if errorlevel 1 goto :fail

echo === mirror 3_1 ===
%PY_CMD% src\sst_dimensionless_ratios.py diagnose --knot-id 3:1:1 --label mirror_trefoil --mirror %COMMON% --output "%OUT%\mirror_trefoil.json"
if errorlevel 1 goto :fail

echo === 4_1 figure-eight ===
%PY_CMD% src\sst_dimensionless_ratios.py diagnose --knot-id 4:1:1 --label figure_eight %COMMON% --output "%OUT%\figure_eight.json"
if errorlevel 1 goto :fail

echo.
echo [OK] Vier statische diagnosebestanden gemaakt.
start "" "%OUT%"
pause
exit /b 0

:fail
echo [ERROR] Een statische diagnose faalde.
pause
exit /b 1
