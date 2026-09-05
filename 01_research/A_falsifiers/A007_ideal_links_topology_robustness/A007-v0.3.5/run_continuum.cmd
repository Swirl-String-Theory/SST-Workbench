@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call scripts\resolve_python.cmd
echo [SST] Native preflight using "%PYTHON%"
"%PYTHON%" run_native_preflight.py
if errorlevel 1 (
  echo [SST] Native preflight failed. Campaign not started.
  exit /b %errorlevel%
)
"%PYTHON%" scripts\run_continuum_cmd.py %*
exit /b %errorlevel%
