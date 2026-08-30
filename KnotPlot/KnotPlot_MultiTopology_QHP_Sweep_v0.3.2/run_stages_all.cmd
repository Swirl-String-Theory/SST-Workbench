@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call run_stage1.cmd %*
if errorlevel 1 exit /b %ERRORLEVEL%
call run_stage2.cmd %*
if errorlevel 1 exit /b %ERRORLEVEL%
call run_stage3.cmd %*
if errorlevel 1 exit /b %ERRORLEVEL%
call run_stage4.cmd %*
exit /b %ERRORLEVEL%
