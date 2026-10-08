@echo off
cd /d "%~dp0"
call run_all.cmd SELFTEST
exit /b %ERRORLEVEL%
