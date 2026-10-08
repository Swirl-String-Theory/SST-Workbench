@echo off
setlocal
cd /d "%~dp0"
set "SST_FALSIFIER_FRAMEWORK_ROOT=%~dp0..\..\..\..\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.4"
set "PY=%~dp0..\.a055-v0.3.1-runtime\Scripts\python.exe"
"%PY%" -m pytest tests -q
if errorlevel 1 exit /b %ERRORLEVEL%
"%PY%" run_instance.py SELFTEST
exit /b %ERRORLEVEL%
