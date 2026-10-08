@echo off
setlocal
cd /d "%~dp0"
if not "%~1"=="" set "SST_WORKBENCH_ROOT=%~1"
call run_all.cmd REVEAL_IF_ALLOWED
exit /b %ERRORLEVEL%
