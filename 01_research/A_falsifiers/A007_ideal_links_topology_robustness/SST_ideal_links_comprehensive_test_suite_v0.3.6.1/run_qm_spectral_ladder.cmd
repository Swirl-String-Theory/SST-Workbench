@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call scripts\resolve_python.cmd
echo [SST] Python interpreter: "%PYTHON%"
"%PYTHON%" run_dependency_preflight.py
if errorlevel 1 exit /b %errorlevel%
echo [SST] Native preflight using "%PYTHON%"
"%PYTHON%" run_native_preflight.py
if errorlevel 1 exit /b %errorlevel%
"%PYTHON%" scripts\run_qm_spectral_ladder.py %*
exit /b %errorlevel%
