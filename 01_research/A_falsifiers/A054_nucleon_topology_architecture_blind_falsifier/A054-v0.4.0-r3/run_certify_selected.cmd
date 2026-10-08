@echo off
setlocal EnableExtensions
for %%I in ("%~dp0.") do set "ROOT=%%~fI"
for %%I in ("%ROOT%\..") do set "FAMILY=%%~fI"
set "PY=%FAMILY%\.venvs\A054-v0.4.0-r3\Scripts\python.exe"
set "WB=%~1"
if "%WB%"=="" if not "%SST_WORKBENCH_ROOT%"=="" set "WB=%SST_WORKBENCH_ROOT%"
if "%WB%"=="" set "WB=C:\workspace\projects\SST-Workbench"
call "%ROOT%\run_00_setup.cmd" "%WB%"
if errorlevel 1 exit /b %ERRORLEVEL%
"%PY%" "%ROOT%\tools\certify_selected.py" --root "%ROOT%"
if errorlevel 1 exit /b %ERRORLEVEL%
set "SST_FALSIFIER_FRAMEWORK_ROOT=%WB%\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.4"
"%PY%" "%ROOT%\run_instance.py" CERTIFY
exit /b %ERRORLEVEL%
