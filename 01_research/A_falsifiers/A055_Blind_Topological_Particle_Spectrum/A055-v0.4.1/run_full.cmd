@echo off
setlocal
cd /d "%~dp0"
if not "%~1"=="" set "SST_WORKBENCH_ROOT=%~1"
call run_all.cmd FULL
exit /b %ERRORLEVEL%
