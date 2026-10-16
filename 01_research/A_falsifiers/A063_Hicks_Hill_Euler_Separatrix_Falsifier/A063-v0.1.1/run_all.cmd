@echo off
setlocal
cd /d "%~dp0"
set "MODE=%~1"
if "%MODE%"=="" set "MODE=BASIC"
if /I "%MODE%"=="SELFTEST" (
  py -3 -m pytest tests -q
  exit /b %errorlevel%
)
if /I not "%MODE%"=="BASIC" if /I not "%MODE%"=="FULL" (
  echo This is a standalone ANALYTIC PROTOTYPE. Use SELFTEST or BASIC / FULL.
  echo Official v1.0.7 FREEZE, CERTIFY and REVEAL are not implemented by this prototype.
  exit /b 2
)
py -3 run_hicks.py
if errorlevel 1 exit /b %errorlevel%
set "OUT=%CD%\A063_Hicks_Hill_Euler_Separatrix_Falsifier_v0.1.1-outputs"
set "REPORT=%CD%\..\A063-v0.1.1_external_reports"
py -3 "..\..\..\..\04_tools\D_proof\SST_Falsifier_Report_Generator\report_generator.py" --outputs "%OUT%" --dest "%REPORT%\external" --catalog A063 --version v0.1.1 --title "Hicks-Hill analytic Euler separatrix controls"

if errorlevel 1 exit /b %errorlevel%
py -3 build_scientific_report.py --outputs "%OUT%" --dest "%REPORT%"
exit /b %errorlevel%
