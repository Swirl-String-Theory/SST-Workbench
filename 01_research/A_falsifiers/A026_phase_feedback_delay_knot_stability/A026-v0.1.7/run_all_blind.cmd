@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "PRESET=%~2"
if "%PRESET%"=="" set "PRESET=basic"

echo ============================================================
echo SST Phase-Delay Knot Stability Falsifier v0.1.7 - BLIND RUN
echo Preset: %PRESET%
echo ============================================================

echo [0/5] Install / native preflight
call run_00_install.cmd || goto :fail

echo [1/5] Resolve dataset + prepare blind IDs
call run_10_prepare_blind.cmd "%~1" "%PRESET%" || goto :fail

echo [2/5] Delay prediction
call run_20_delay_predict.cmd "%PRESET%" || goto :fail

echo [3/5] Nonlinear measurement
call run_30_nonlinear_measure.cmd "%PRESET%" || goto :fail

echo [4/5] Freeze and evaluate
call run_35_freeze_and_evaluate.cmd
set "RC=%ERRORLEVEL%"

echo ============================================================
echo BLIND RUN COMPLETE. Results are frozen. Reveal has NOT run.
echo Primary result: results\BLIND_EVALUATION.json
echo Reveal key hash: blind_work\reveal_key_sha256.txt
echo ============================================================
exit /b %RC%

:fail
echo FAILED before blind freeze.
exit /b 1
