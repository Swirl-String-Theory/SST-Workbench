@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" tests\selftest.py
if errorlevel 1 exit /b %ERRORLEVEL%
".venv\Scripts\python.exe" validate_parameter_syntax.py
exit /b %ERRORLEVEL%
