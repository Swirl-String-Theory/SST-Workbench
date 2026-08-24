@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ============================================================
echo KnotPlot 3.1 Trefoil Seed Campaign v0.1.3
echo 38 preregistered seeds - known-good KnotPlot KPC syntax only
echo ============================================================

call run_00_install.cmd
if errorlevel 1 exit /b %ERRORLEVEL%

call run_03_selftest.cmd
if errorlevel 1 exit /b %ERRORLEVEL%

call run_02_verify_preregistration.cmd
if errorlevel 1 exit /b %ERRORLEVEL%

call run_05_export_base.cmd
if errorlevel 1 exit /b %ERRORLEVEL%

call run_10_generate_seeds.cmd
if errorlevel 1 exit /b %ERRORLEVEL%

call run_15_generate_kpc.cmd
if errorlevel 1 exit /b %ERRORLEVEL%

call run_16_validate_kpc_syntax.cmd
if errorlevel 1 exit /b %ERRORLEVEL%

call run_20_relax.cmd
if errorlevel 1 exit /b %ERRORLEVEL%

call run_30_analyze.cmd
set "ANRC=%ERRORLEVEL%"

call run_40_pack_outputs.cmd
if errorlevel 1 exit /b %ERRORLEVEL%

echo ============================================================
if "%ANRC%"=="0" (
  echo CAMPAIGN COMPLETE - DATASET ELIGIBLE FOR PHASE-DELAY PREVIEW
) else (
  echo CAMPAIGN COMPLETE - DATASET GENERATED BUT NOVELTY GATE NOT MET
)
echo See analysis\REPORT.md
echo ============================================================
exit /b %ANRC%
