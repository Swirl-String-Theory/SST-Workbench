@echo off
setlocal
cd /d "%~dp0"
set "MODE=%~1"
if "%MODE%"=="" set "MODE=FULL"
if /I "%MODE%"=="SELFTEST" (
    py -3 -m pytest tests -q
    if errorlevel 1 exit /b 1
    exit /b 0
)
if /I not "%MODE%"=="BASIC" if /I not "%MODE%"=="FULL" (
    echo Supported modes: SELFTEST BASIC FULL
    echo C++ native CERTIFY or canonical v1.0.7 FREEZE are NOT implemented.
    exit /b 2
)
py -3 run_invariant.py --mode %MODE%
if errorlevel 1 exit /b %errorlevel%
py -3 generate_report.py
exit /b %errorlevel%
