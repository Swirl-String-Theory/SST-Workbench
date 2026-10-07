@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" goto ALL
if /I "%~1"=="SETUP" goto SETUP
if /I "%~1"=="SELFTEST" goto SELFTEST
if /I "%~1"=="BACKENDS" goto BACKENDS
if /I "%~1"=="ALL" goto ALL
echo Usage: run_all.cmd [SETUP^|SELFTEST^|BACKENDS^|ALL]
exit /b 2
:SETUP
call run_00_setup.cmd
exit /b %ERRORLEVEL%
:SELFTEST
call run_01_selftest.cmd
exit /b %ERRORLEVEL%
:BACKENDS
call run_02_backend_selftest.cmd
exit /b %ERRORLEVEL%
:ALL
call run_00_setup.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_01_selftest.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_02_backend_selftest.cmd
exit /b %ERRORLEVEL%
