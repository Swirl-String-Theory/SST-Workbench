@echo off
setlocal
set "WB=%~1"
if "%WB%"=="" if not "%SST_WORKBENCH_ROOT%"=="" set "WB=%SST_WORKBENCH_ROOT%"
if "%WB%"=="" set "WB=C:\workspace\projects\SST-Workbench"
call "%~dp0run_00_setup.cmd" "%WB%" || exit /b %errorlevel%
"%~dp0.venv\Scripts\python.exe" "%~dp0tools\certify_selected.py" --root "%~dp0" || exit /b %errorlevel%
set "SST_FALSIFIER_FRAMEWORK_ROOT=%WB%\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.4"
"%~dp0.venv\Scripts\python.exe" "%~dp0run_instance.py" CERTIFY
endlocal
