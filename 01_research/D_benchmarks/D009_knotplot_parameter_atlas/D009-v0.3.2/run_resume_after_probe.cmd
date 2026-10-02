@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ============================================================
echo Atlas v0.3.2 - resume after completed v0.3.1 probe
echo Reuses existing out\probe and logs\probe; does NOT rerun 181 probes.
echo ============================================================

if not exist ".venv\Scripts\python.exe" (
  echo ERROR: .venv missing. Run run_00_install.cmd first.
  exit /b 5
)

if not exist "logs\probe" (
  echo ERROR: logs\probe missing.
  exit /b 6
)

".venv\Scripts\python.exe" analyze.py probe
if errorlevel 1 exit /b %ERRORLEVEL%

call run_30_extended.cmd
if errorlevel 1 exit /b %ERRORLEVEL%

call run_40_analyze_extended.cmd
if errorlevel 1 exit /b %ERRORLEVEL%

call run_90_pack_outputs.cmd
if errorlevel 1 exit /b %ERRORLEVEL%

echo ============================================================
echo RESUME COMPLETE
echo See analysis\PROBE.md and analysis\EXTENDED.md
echo ============================================================
exit /b 0
