@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" goto SELFTEST
if /I "%~1"=="SETUP" goto SETUP
if /I "%~1"=="SELFTEST" goto SELFTEST
echo Usage: run_all.cmd [SETUP^|SELFTEST]
exit /b 2
:SETUP
call run_00_setup.cmd
if errorlevel 1 exit /b %errorlevel%
:SELFTEST
call run_01_selftest.cmd
exit /b %errorlevel%
