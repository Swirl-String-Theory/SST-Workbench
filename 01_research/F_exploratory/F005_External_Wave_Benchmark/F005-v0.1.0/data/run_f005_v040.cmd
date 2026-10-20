@echo off
setlocal
cd /d "%~dp0.."
where py >nul 2>&1
if errorlevel 1 (
  echo Python launcher py.exe not found. Install Python 3.10+.
  exit /b 2
)
py -3 data\f005_free_run_family_v0.4.0.py --root . %*
if errorlevel 1 (
  echo F005 v0.4.0 BLOCKED - check console messages. Never interpret partial outputs as certification.
  exit /b 1
)
echo F005 v0.4.0 completed. Outputs in outputs\f005_free_run_family_v0.4.0\
endlocal
