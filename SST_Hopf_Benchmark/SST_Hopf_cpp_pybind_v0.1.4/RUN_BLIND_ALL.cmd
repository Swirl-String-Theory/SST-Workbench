@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo SST Hopf v0.1.4 BLIND campaign
echo No SST target inputs are read by this workflow.
echo ============================================================
if not exist "blind_inputs\candidate_pack_manifest.json" (
  echo [1/4] Preparing anonymized candidates...
  call "PREPARE_BLIND_CAMPAIGN.cmd"
  if errorlevel 1 goto :fail
) else (
  echo [1/4] Existing anonymized candidate pack retained.
)
echo [2/4] Native backend...
call "cmd\_ENSURE_NATIVE.cmd"
if errorlevel 1 goto :fail
echo [3/4] Running blind H0-H5/topology campaign...
.venv\Scripts\python.exe run_blind_campaign.py
if errorlevel 1 goto :fail
echo [4/4] Sealing results...
.venv\Scripts\python.exe seal_blind_results.py
if errorlevel 1 goto :fail
echo ============================================================
echo BLIND CAMPAIGN SEALED.
echo You may now fill sst_reveal.json and run RUN_SST_REVEAL.cmd
echo ============================================================
exit /b 0
:fail
echo ============================================================
echo BLIND CAMPAIGN FAILED - DO NOT REVEAL.
echo ============================================================
exit /b 1
