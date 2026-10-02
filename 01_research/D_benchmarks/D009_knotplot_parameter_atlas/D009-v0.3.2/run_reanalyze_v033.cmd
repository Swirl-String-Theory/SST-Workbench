@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ============================================================
echo Atlas v0.3.3 analysis-only reanalysis
echo Reuses existing out\probe, out\extended and logs.
echo No KnotPlot relaxation is rerun.
echo ============================================================

if not exist ".venv\Scripts\python.exe" (
  echo ERROR: .venv missing. Run run_00_install.cmd first.
  exit /b 5
)
if not exist "out\extended" (
  echo ERROR: out\extended missing. Overlay this patch onto the completed v0.3.2 campaign folder.
  exit /b 6
)

".venv\Scripts\python.exe" analyze.py probe
if errorlevel 1 exit /b %ERRORLEVEL%

".venv\Scripts\python.exe" analyze.py extended
if errorlevel 1 exit /b %ERRORLEVEL%

".venv\Scripts\python.exe" balance_candidates.py
if errorlevel 1 exit /b %ERRORLEVEL%

echo ============================================================
echo REANALYSIS COMPLETE
echo See:
echo   analysis\EXTENDED.md
echo   analysis\BALANCE_CANDIDATES.md
echo ============================================================
exit /b 0
