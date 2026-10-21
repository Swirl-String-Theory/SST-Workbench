@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set TIER=%~1
if "%TIER%"=="" set TIER=BASIC
py -3 -c "import numpy,scipy,sympy,shapely,matplotlib" >nul 2>&1 || (
  echo [FAIL] Python requirements missing. Run: py -3 -m pip install -r requirements.txt
  exit /b 2
)
if /I "%TIER%"=="BASIC" (
  py -3 src\build.py --mode ALL --n 1024 --borromean-n 768 || exit /b 1
) else if /I "%TIER%"=="FULL" (
  py -3 src\build.py --mode ALL --n 2048 --borromean-n 1536 || exit /b 1
) else if /I "%TIER%"=="SMOKE" (
  py -3 src\build.py --mode INDIVIDUAL --m 3 4 --n 512 || exit /b 1
) else if /I "%TIER%"=="TEST" (
  echo Test only
) else (
  echo Unsupported tier: %TIER% . BASIC FULL SMOKE TEST allowed.
  exit /b 2
)
py -3 -m unittest discover -s tests -v || exit /b 1
py -3 src\preview.py || exit /b 1
echo [PASS] DEVELOPMENT static geometry only. KnotPlot runtime, independent 3D isotopy and Euler dynamics NOT certified.
endlocal
