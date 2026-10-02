@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ============================================================
echo Trefoil v0.2.3.2 recovery
echo Reusing completed 100k-200k continuation outputs
echo Running ANALYZE + PACK only
echo ============================================================
call run_40_analyze.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_90_pack_outputs.cmd
exit /b %ERRORLEVEL%
