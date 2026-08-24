@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo KnotPlot Parameter Atlas v0.3.2 - RESUME AFTER PROBE
echo ============================================================

if not exist logs\probe (
  echo ERROR: logs\probe is missing. No probe campaign to resume.
  exit /b 2
)

if not exist out\probe (
  echo ERROR: out\probe is missing. No probe outputs to analyze.
  exit /b 2
)

call run_20_analyze_probe.cmd
if errorlevel 1 exit /b %ERRORLEVEL%

call run_30_extended.cmd
if errorlevel 1 exit /b %ERRORLEVEL%

call run_40_analyze_extended.cmd
if errorlevel 1 exit /b %ERRORLEVEL%

call run_90_pack_outputs.cmd
if errorlevel 1 exit /b %ERRORLEVEL%

echo ============================================================
echo RESUME COMPLETE
echo Existing probe data was reused; probe stage was NOT rerun.
echo ============================================================
exit /b 0
