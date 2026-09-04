@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if "%~1"=="" echo Usage: run_hr_ladder_analyze.cmd ^<completed_output_dir^> & exit /b 2
if not exist ".venv\Scripts\python.exe" call run_install.cmd || exit /b 1
".venv\Scripts\python.exe" tools\analyze_hr_ladder.py "%~1"
exit /b %errorlevel%
