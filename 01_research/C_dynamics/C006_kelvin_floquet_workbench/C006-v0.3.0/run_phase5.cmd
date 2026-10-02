@echo off
setlocal
cd /d "%~dp0"
set PRESET=quick
if /I "%~1"=="full" set PRESET=full
if not exist ".venv\Scripts\python.exe" call "cmd\00_SETUP_VENV.cmd" || exit /b 1
.venv\Scripts\python.exe run_phase5.py --preset %PRESET% --out-dir "audit_out_phase5_%PRESET%\phase5" --phase2-summary "audit_out_phase5_%PRESET%\phase2\phase2_summary.json"
exit /b %errorlevel%
