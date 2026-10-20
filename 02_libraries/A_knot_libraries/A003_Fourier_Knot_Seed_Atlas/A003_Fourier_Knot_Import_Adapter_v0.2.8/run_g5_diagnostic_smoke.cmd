@echo off
setlocal
call "%~dp0run_g5_diagnostic.cmd" --skip-provider
exit /b %errorlevel%
