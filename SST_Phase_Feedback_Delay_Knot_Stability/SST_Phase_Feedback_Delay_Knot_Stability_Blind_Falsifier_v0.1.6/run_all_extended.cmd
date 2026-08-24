@echo off
setlocal
cd /d "%~dp0"
call run_all.cmd "%~1" extended
exit /b %ERRORLEVEL%
