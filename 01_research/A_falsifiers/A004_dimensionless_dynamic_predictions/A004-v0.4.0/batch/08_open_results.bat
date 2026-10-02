@echo off
setlocal
call "%~dp0_common.bat"
if errorlevel 1 exit /b 1
if not exist "%ROOT%\outputs" mkdir "%ROOT%\outputs"
start "" "%ROOT%\outputs"
exit /b 0
