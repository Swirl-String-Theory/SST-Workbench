@echo off
setlocal
cd /d "%~dp0\.."
if not exist ".venv\Scripts\python.exe" call "cmd\00_SETUP_VENV.cmd"
if errorlevel 1 exit /b 1
call ".venv\Scripts\activate.bat"
python benchmark_cpp_vs_python.py 48
exit /b %errorlevel%
