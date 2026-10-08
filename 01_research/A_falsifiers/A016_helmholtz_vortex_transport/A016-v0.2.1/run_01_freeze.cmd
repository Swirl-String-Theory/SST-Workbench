@echo off
cd /d "%~dp0"
call run_all.cmd FREEZE
exit /b %ERRORLEVEL%
