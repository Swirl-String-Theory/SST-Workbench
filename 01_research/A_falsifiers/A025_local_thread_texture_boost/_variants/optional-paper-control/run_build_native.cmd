@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call run_install.cmd
if errorlevel 1 exit /b %errorlevel%
.venv\Scripts\python.exe -m sst_thread_falsifier.native_ext.build_ext_if_needed --force --strict
exit /b %errorlevel%
