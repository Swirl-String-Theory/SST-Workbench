@echo off
setlocal EnableExtensions
for %%I in ("%~dp0.") do set "ROOT=%%~fI"
for %%I in ("%ROOT%\..") do set "FAMILY=%%~fI"
set "PY=%FAMILY%\.venvs\A054-v0.4.0-r3\Scripts\python.exe"
set "MODE=%~1"
set "WB=%~2"
if /I "%MODE%"=="" set "MODE=BASIC"
if /I not "%MODE%"=="BASIC" if /I not "%MODE%"=="FULL" if /I not "%MODE%"=="CERTIFY" if /I not "%MODE%"=="REVEAL" (set "WB=%~1" & set "MODE=BASIC")
if "%WB%"=="" if not "%SST_WORKBENCH_ROOT%"=="" set "WB=%SST_WORKBENCH_ROOT%"
if "%WB%"=="" set "WB=C:\workspace\projects\SST-Workbench"

call "%ROOT%\run_00_setup.cmd" "%WB%"
if errorlevel 1 exit /b %ERRORLEVEL%
if not exist "%PY%" exit /b 20

set "SST_FALSIFIER_FRAMEWORK_ROOT=%WB%\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.4"
"%PY%" "%ROOT%\run_instance.py" FREEZE
if errorlevel 1 exit /b %ERRORLEVEL%
"%PY%" "%ROOT%\run_instance.py" %MODE%
exit /b %ERRORLEVEL%
