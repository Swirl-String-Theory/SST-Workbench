@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
  if errorlevel 1 exit /b 1
  .venv\Scripts\python.exe -m pip install -r requirements.txt
  if errorlevel 1 exit /b 1
)
set "PYTHONPATH=%CD%"
set "MODE=%~1"
if "%MODE%"=="" set "MODE=SELFTEST"
if /I "%MODE%"=="SELFTEST" ( .venv\Scripts\python.exe -m pytest -q & exit /b !ERRORLEVEL! )
if /I "%MODE%"=="CENSUS" ( .venv\Scripts\python.exe -m src.library_census & exit /b !ERRORLEVEL! )
if /I "%MODE%"=="LONG" ( .venv\Scripts\python.exe -m src.long_euler & exit /b !ERRORLEVEL! )
if /I "%MODE%"=="ASSESS" ( .venv\Scripts\python.exe -m src.qualification & exit /b !ERRORLEVEL! )
if /I "%MODE%"=="EULER_ALL_SCREEN" ( .venv\Scripts\python.exe -m src.batch_all_euler %2 %3 %4 %5 %6 %7 %8 %9 & exit /b !ERRORLEVEL! )
if /I "%MODE%"=="REPORT" ( .venv\Scripts\python.exe -m src.release & exit /b !ERRORLEVEL! )
echo Unsupported mode. Allowed: SELFTEST CENSUS LONG ASSESS EULER_ALL_SCREEN REPORT
exit /b 2
