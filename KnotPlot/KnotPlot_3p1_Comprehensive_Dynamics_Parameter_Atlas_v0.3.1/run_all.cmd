@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ============================================================
echo KnotPlot 3.1 Comprehensive Dynamics Parameter Atlas v0.3.1
echo syntax-verified rebuild from parameters_full runtime dump
echo ============================================================

call run_00_install.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_filesystem_preflight.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_00_generate.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_05_validate_parameter_syntax.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_dry.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_10_probe.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_20_analyze_probe.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_30_extended.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_40_analyze_extended.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_90_pack_outputs.cmd
if errorlevel 1 exit /b %ERRORLEVEL%

echo ============================================================
echo DONE - see analysis\PROBE.md and analysis\EXTENDED.md
echo ============================================================
exit /b 0
