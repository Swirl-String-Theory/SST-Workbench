@echo off
setlocal
set "MODE=%~1"
set "WB=%~2"
if /I "%MODE%"=="" set "MODE=BASIC"
if /I not "%MODE%"=="BASIC" if /I not "%MODE%"=="FULL" if /I not "%MODE%"=="CERTIFY" if /I not "%MODE%"=="REVEAL" (set "WB=%~1" & set "MODE=BASIC")
if "%WB%"=="" if not "%SST_WORKBENCH_ROOT%"=="" set "WB=%SST_WORKBENCH_ROOT%"
if "%WB%"=="" set "WB=C:\workspace\projects\SST-Workbench"
call "%~dp0run_00_setup.cmd" "%WB%" || exit /b %errorlevel%
set "SST_FALSIFIER_FRAMEWORK_ROOT=%WB%\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.4"
"%~dp0.venv\Scripts\python.exe" "%~dp0run_instance.py" FREEZE || exit /b %errorlevel%
"%~dp0.venv\Scripts\python.exe" "%~dp0run_instance.py" %MODE%
endlocal
