@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call run_install.cmd || exit /b 1
call run_extended.cmd --backend openmp %*
exit /b %errorlevel%
