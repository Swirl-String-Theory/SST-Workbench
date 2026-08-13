@echo off
setlocal
cd /d "%~dp0\.."
if not exist ".venv\Scripts\python.exe" call "cmd\00_SETUP_VENV.cmd"
if errorlevel 1 exit /b 1
call ".venv\Scripts\activate.bat"
set SST_HOPF_FORCE_PYTHON=0
set SST_HOPF_FORCE_BUILD=1
set SST_HOPF_BUILD_VERBOSE=1
python -m sst_hopf_native.build_ext_if_needed --force --strict
if errorlevel 1 exit /b 1
python -c "from sst_hopf_native import backend_info; print(backend_info())"
exit /b %errorlevel%
