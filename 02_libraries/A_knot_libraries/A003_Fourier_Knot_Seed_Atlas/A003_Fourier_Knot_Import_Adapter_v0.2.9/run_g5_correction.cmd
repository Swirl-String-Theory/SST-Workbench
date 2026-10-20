@echo off
setlocal EnableExtensions
call "%~dp0run_g5_diagnostic.cmd" %*
exit /b %errorlevel%
