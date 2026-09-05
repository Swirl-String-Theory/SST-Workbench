@echo off
setlocal
call "%~dp002_selftest.bat"
if errorlevel 1 exit /b 1
call "%~dp004_diagnose_all_knots.bat"
if errorlevel 1 exit /b 1
call "%~dp005_evolve_trefoil.bat"
if errorlevel 1 exit /b 1
call "%~dp006_medium_campaign.bat"
if errorlevel 1 exit /b 1
echo [OK] Diagnose-, evolutie- en medium-convergentiepijplijn voltooid.
pause
