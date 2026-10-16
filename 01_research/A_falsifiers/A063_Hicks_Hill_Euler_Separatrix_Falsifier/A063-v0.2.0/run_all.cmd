@echo off
setlocal
cd /d "%~dp0"
set "MODE=%~1"
if "%MODE%"=="" set "MODE=FULL"
if /I "%MODE%"=="SELFTEST" (
 py -3 -m pytest tests -q
 exit /b %errorlevel%
)
if /I not "%MODE%"=="BASIC" if /I not "%MODE%"=="FULL" (
 echo Only BASIC, FULL, SELFTEST supported. v1.0.7 FREEZE/CERTIFY not yet available.
 exit /b 2
)
py -3 run_tube.py --mode %MODE%
if errorlevel 1 exit /b %errorlevel%
py -3 generate_report.py
exit /b %errorlevel%
