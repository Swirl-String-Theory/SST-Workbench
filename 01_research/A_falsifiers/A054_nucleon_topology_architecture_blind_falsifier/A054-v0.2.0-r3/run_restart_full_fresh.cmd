@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
if "%~1"=="" (echo Usage: run_restart_full_fresh.cmd ^<existing-campaign-dir^> & exit /b 2)
set "PY=%CD%\.venv\Scripts\python.exe"
if not exist "%PY%" (echo [ERROR] Missing .venv. Run run_00_install.cmd first. & exit /b 2)
"%PY%" tools\check_backend.py --policy require_openmp || exit /b !errorlevel!
"%PY%" tools\preflight_isolated_backend.py || exit /b !errorlevel!
call run_03_certify.cmd "%~1" full fresh || exit /b !errorlevel!
call run_90_pack_blind.cmd "%~1" || exit /b !errorlevel!
echo FRESH FULL COMPLETE. STOPPED BEFORE REVEAL by design.
exit /b 0
