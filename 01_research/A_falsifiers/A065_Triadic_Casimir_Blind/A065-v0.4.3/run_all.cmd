@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto local_python
if defined VIRTUAL_ENV if exist "%VIRTUAL_ENV%\Scripts\python.exe" goto active_python
where py >nul 2>nul
if not errorlevel 1 goto py_launcher
python run_python.py %*
exit /b %errorlevel%
:local_python
".venv\Scripts\python.exe" run_python.py %*
exit /b %errorlevel%
:active_python
"%VIRTUAL_ENV%\Scripts\python.exe" run_python.py %*
exit /b %errorlevel%
:py_launcher
py -3 run_python.py %*
exit /b %errorlevel%
