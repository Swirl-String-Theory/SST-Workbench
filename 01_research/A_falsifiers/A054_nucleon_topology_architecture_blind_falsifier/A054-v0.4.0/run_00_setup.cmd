@echo off
setlocal
set "ROOT=%~dp0"
set "WB=%~1"
if "%WB%"=="" if not "%SST_WORKBENCH_ROOT%"=="" set "WB=%SST_WORKBENCH_ROOT%"
if "%WB%"=="" set "WB=C:\workspace\projects\SST-Workbench"
set "FW=%WB%\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.4"
if not exist "%FW%\PACKAGE_MANIFEST.json" (echo [ERROR] Framework v1.0.4 not found: %FW% & exit /b 2)
if not exist "%ROOT%.venv\Scripts\python.exe" py -3 -m venv "%ROOT%.venv"
"%ROOT%.venv\Scripts\python.exe" -m pip install -U pip setuptools wheel pybind11 numpy pytest
"%ROOT%.venv\Scripts\python.exe" -m pip install -e "%FW%" -e "%ROOT%"
set "SST_FALSIFIER_FRAMEWORK_ROOT=%FW%"
"%ROOT%.venv\Scripts\python.exe" "%ROOT%run_instance.py" SELFTEST
endlocal
