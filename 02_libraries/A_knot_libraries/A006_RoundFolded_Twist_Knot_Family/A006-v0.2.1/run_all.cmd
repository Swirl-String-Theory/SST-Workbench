@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set TIER=%~1
if "%TIER%"=="" set TIER=BASIC
if /I "%TIER%"=="SMOKE" (set N=256) else if /I "%TIER%"=="BASIC" (set N=512) else if /I "%TIER%"=="FULL" (set N=1024) else (echo Usage: run_all.cmd SMOKE ^| BASIC ^| FULL & exit /b 2)
py -3 -c "import numpy,scipy,sympy,shapely" >nul 2>&1 || (echo Dependencies missing: py -3 -m pip install -r requirements.txt & exit /b 2)
py -3 src\build.py --n %N% || exit /b 1
py -3 -m unittest discover -s tests -v || exit /b 1
echo [PASS] Static individual TikZ geometry only. KnotPlot runtime and Euler are NOT certified.
endlocal
