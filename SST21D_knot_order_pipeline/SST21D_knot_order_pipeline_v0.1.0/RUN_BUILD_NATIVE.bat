@echo off
setlocal
cd /d "%~dp0"
py -3 -m pip install -e . --no-build-isolation
if errorlevel 1 exit /b %errorlevel%
py -3 -m sst21d build-native
pause
