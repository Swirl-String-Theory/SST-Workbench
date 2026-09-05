@echo off
setlocal
cd /d "%~dp0"
py -3 -m pip install -e . --no-build-isolation
if errorlevel 1 goto :error
py -3 -m sstcbhf demo --thresholds-json configs\default_thresholds.json --out outputs\demo_torus_trefoil
set RC=%ERRORLEVEL%
echo.
echo Demo finished with exit code %RC%.
pause
exit /b %RC%
:error
echo Installation failed.
pause
exit /b 1
