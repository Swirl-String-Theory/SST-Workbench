@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ============================================================
echo Trefoil v0.2.1 metric-neutral 30k to 60k continuation repair
echo Existing 0..30k states are preserved.
echo ============================================================
call run_02_verify_preregistration.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_extended_only.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_40_analyze.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_90_pack_outputs.cmd
exit /b %ERRORLEVEL%
