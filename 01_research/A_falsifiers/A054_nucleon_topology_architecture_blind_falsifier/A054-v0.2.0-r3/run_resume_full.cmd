@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
set "PY=%CD%\.venv\Scripts\python.exe"
if not exist "%PY%" (echo [ERROR] Missing .venv. Run run_00_install.cmd first. & exit /b 2)
"%PY%" tools\check_backend.py --policy require_openmp || exit /b !errorlevel!
"%PY%" tools\preflight_isolated_backend.py || exit /b !errorlevel!
set "CAMP=%~1"
if "!CAMP!"=="" (
  set "BASE=A054_Nucleon_Topology_Architecture_Blind_Falsifier_v0.2.0-outputs"
  for /f "delims=" %%D in ('dir /b /ad /o-d "!BASE!\full_*" 2^>nul') do if not defined CAMP set "CAMP=!BASE!\%%D"
)
if "!CAMP!"=="" (echo [ERROR] No FULL campaign found. Pass the campaign directory explicitly. & exit /b 2)
if not exist "!CAMP!\BLIND_MANIFEST.json" (echo [ERROR] Not a prepared A054 campaign: !CAMP! & exit /b 2)
echo [INFO] Resuming FULL campaign: !CAMP!
call run_03_certify.cmd "!CAMP!" full resume || exit /b !errorlevel!
call run_90_pack_blind.cmd "!CAMP!" || exit /b !errorlevel!
echo RESUME COMPLETE. STOPPED BEFORE REVEAL by design.
exit /b 0
