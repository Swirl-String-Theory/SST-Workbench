@echo off
setlocal
cd /d "%~dp0"
py -3 src\build.py --tier ALL
if errorlevel 1 exit /b %errorlevel%
py -3 -m unittest discover -s tests -v
if errorlevel 1 exit /b %errorlevel%
echo BUILD STATIC QA PASS - KNOTPLOT RUNTIME NOT TESTED
echo Next: read diagnostic/00_solver_trefoil_smoke.kpc in KnotPlot
exit /b 0
