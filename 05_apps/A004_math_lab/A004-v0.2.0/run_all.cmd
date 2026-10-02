@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ============================================================
echo SST Math Lab v0.2.0 - install + server start
echo ============================================================
call install_libs.cmd
if errorlevel 1 exit /b 1
call run_server.cmd
exit /b %errorlevel%
