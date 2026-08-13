@echo off
setlocal
cd /d "%~dp0"
if not exist "blind_inputs\candidate_pack_manifest.json" call "PREPARE_BLIND_CAMPAIGN.cmd"
if errorlevel 1 exit /b 1
call "cmd\_ENSURE_NATIVE.cmd"
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe run_blind_candidates.py --output results\blind_topology
exit /b %errorlevel%
