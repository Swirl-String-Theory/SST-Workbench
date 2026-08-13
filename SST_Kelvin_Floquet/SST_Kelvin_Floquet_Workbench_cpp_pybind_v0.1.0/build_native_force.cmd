@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call "cmd\00_SETUP_VENV.cmd"
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m sst_kelvin_workbench.build_ext_if_needed --force --strict
exit /b %errorlevel%
