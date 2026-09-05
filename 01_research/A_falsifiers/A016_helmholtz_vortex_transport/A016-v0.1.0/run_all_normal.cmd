@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call run_00_install.cmd
if errorlevel 1 exit /b %errorlevel%
call run_06_synthetic_controls.cmd
if errorlevel 1 exit /b %errorlevel%
call run_90_tests.cmd
if errorlevel 1 exit /b %errorlevel%
call run_02_normal.cmd
if errorlevel 1 exit /b %errorlevel%
echo [H-SST] ALL PASS - campaign completed. Scientific PASS/FALSIFIED status is inside frozen_result.json.
exit /b 0
