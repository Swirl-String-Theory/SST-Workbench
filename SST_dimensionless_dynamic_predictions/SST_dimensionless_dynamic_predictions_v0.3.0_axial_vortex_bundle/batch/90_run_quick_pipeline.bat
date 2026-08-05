@echo off
setlocal
call "%~dp001_setup_venv.bat"
if errorlevel 1 exit /b 1
call "%~dp002_selftest.bat"
if errorlevel 1 exit /b 1
call "%~dp003_quick_campaign.bat"
if errorlevel 1 exit /b 1
echo [OK] Installatie, selftest en quick campaign zijn voltooid.
pause
