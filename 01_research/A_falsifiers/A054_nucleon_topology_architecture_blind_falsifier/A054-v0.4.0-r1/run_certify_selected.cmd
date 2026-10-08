@echo off
setlocal EnableExtensions
for %%I in ("%~dp0.") do set "ROOT=%%~fI"
set "WB=%~1"
if "%WB%"=="" if not "%SST_WORKBENCH_ROOT%"=="" set "WB=%SST_WORKBENCH_ROOT%"
if "%WB%"=="" set "WB=C:\workspace\projects\SST-Workbench"
call "%ROOT%\run_00_setup.cmd" "%WB%"
if errorlevel 1 (set "RC=%ERRORLEVEL%" & endlocal & exit /b %RC%)
"%ROOT%\.venv\Scripts\python.exe" "%ROOT%\tools\certify_selected.py" --root "%ROOT%"
if errorlevel 1 (set "RC=%ERRORLEVEL%" & endlocal & exit /b %RC%)
set "SST_FALSIFIER_FRAMEWORK_ROOT=%WB%\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.4"
"%ROOT%\.venv\Scripts\python.exe" "%ROOT%\run_instance.py" CERTIFY
set "RC=%ERRORLEVEL%"
endlocal & exit /b %RC%
