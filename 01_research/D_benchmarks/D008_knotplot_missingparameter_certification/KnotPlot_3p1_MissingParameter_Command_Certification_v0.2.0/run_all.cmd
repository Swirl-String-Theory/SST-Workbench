@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo KnotPlot Missing-Parameter Certification v0.2.1
echo ============================================================

call run_00_certify.cmd
if errorlevel 1 exit /b %ERRORLEVEL%

call run_10_analyze_certification.cmd
if errorlevel 1 exit /b %ERRORLEVEL%

call run_20_extended_certified.cmd
if errorlevel 1 exit /b %ERRORLEVEL%

if exist analysis\EXTENDED_SKIPPED.flag goto :pack

call run_30_analyze_extended.cmd
if errorlevel 1 exit /b %ERRORLEVEL%

:pack
call run_90_pack_outputs.cmd
if errorlevel 1 exit /b %ERRORLEVEL%

echo ============================================================
echo DONE
echo See analysis\CERTIFICATION.md
if not exist analysis\EXTENDED_SKIPPED.flag echo See analysis\EXTENDED.md
if exist analysis\EXTENDED_SKIPPED.flag echo Extended stage was correctly skipped.
echo ============================================================
exit /b 0
