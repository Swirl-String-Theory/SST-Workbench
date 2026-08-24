@echo off
setlocal EnableExtensions
cd /d "%~dp0"
python run_matrix_batch.py --one 00_baseline_MEB_tight.kpc --dry-run >nul 2>nul
rem The real runtime preflight is automatically run at the start of any non-dry discovery.
rem This wrapper runs one real script after the preflight only when /run is supplied.
if /I "%~1"=="/run" (
  python run_matrix_batch.py --one 00_baseline_MEB_tight.kpc
  exit /b %ERRORLEVEL%
)
echo Runtime preflight is automatic at the start of run_fresh_discovery.cmd.
echo Use: run_preflight.cmd /run   to preflight + execute baseline only.
exit /b 0
