@echo off
setlocal
cd /d "%~dp0"
call run_python.cmd -m experiment.pklsa %*
exit /b %ERRORLEVEL%
