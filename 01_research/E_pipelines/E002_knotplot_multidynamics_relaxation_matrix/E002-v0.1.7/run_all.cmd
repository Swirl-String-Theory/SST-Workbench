@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ============================================================
echo KnotPlot 3.1 MultiDynamics Relaxation Matrix v0.1.7
echo 41 syntax-corrected 10k candidates
echo ============================================================
call run_00_install.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_05_generate.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_10_validate_syntax.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_30_matrix.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_40_analyze.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_90_pack_outputs.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
echo DONE - see analysis\REPORT.md
exit /b 0
