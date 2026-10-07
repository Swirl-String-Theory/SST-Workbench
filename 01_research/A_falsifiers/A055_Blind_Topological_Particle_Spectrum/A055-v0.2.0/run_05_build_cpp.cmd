@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe call run_00_install.cmd || exit /b 1
.venv\Scripts\python.exe setup.py build_ext --inplace
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -c "import a055_native; print('native import PASS')"
exit /b %ERRORLEVEL%
