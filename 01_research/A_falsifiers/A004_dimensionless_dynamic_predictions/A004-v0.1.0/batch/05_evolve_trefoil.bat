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

set "OUT=%ROOT%\outputs\single_evolution"
if not exist "%OUT%" mkdir "%OUT%"
echo === Trefoil korte dynamische evolutie ===
%PY_CMD% src\sst_dimensionless_ratios.py evolve ^
  --knot-id 3:1:1 ^
  --label trefoil ^
  --ideal-file data\ideal_favorites.txt ^
  --resolution 128 ^
  --epsilon 0.08 ^
  --kernel winckelmans ^
  --normalization fixed_length ^
  --dt 0.00025 ^
  --steps 400 ^
  --sample-every 10 ^
  --remesh-every 1 ^
  --output "%OUT%\trefoil_evolution.json"
if errorlevel 1 goto :fail

echo.
echo [OK] Evolutie-uitvoer:
echo %OUT%\trefoil_evolution.json
start "" "%OUT%"
pause
exit /b 0

:fail
echo [ERROR] Evolutie faalde.
pause
exit /b 1
