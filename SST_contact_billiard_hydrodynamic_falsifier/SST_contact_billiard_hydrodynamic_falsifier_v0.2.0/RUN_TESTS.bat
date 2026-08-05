@echo off
setlocal
cd /d "%~dp0"
py -3 -m pip install -e ".[test]" --no-build-isolation
if errorlevel 1 goto :error
py -3 -m pytest
set RC=%ERRORLEVEL%
pause
exit /b %RC%
:error
echo Installation failed.
pause
exit /b 1
