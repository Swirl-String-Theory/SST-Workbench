@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PRESET=%~2"
if "%PRESET%"=="" set "PRESET=basic"
set "MODE=%~3"
if "%MODE%"=="" set "MODE=confirmatory"
echo ============================================================
echo SST Phase-Delay Knot Stability Falsifier v0.2.0 - BLIND RUN
echo Preset: %PRESET%   Mode: %MODE%
echo ============================================================
echo [0/6] Install / native preflight
call run_00_install.cmd || goto :fail
echo [1/6] Verify frozen preregistration
call run_08_verify_preregistration.cmd || goto :fail
echo [2/6] Deduplicate / novelty filter / blind
call run_10_prepare_blind.cmd "%~1" "%PRESET%" "%MODE%" || goto :fail
echo [3/6] Independent Kelvin packet delay prediction
call run_20_packet_delay_predict.cmd "%PRESET%" || goto :fail
echo [4/6] Unforced nonlinear stability measurement
call run_30_nonlinear_measure.cmd "%PRESET%" || goto :fail
echo [5/6] Freeze + blind evaluation
call run_35_freeze_and_evaluate.cmd
set "RC=%ERRORLEVEL%"
echo ============================================================
echo BLIND RUN COMPLETE. Reveal has NOT run.
echo Primary: results\BLIND_EVALUATION.json
echo ============================================================
exit /b %RC%
:fail
echo FAILED before blind freeze.
exit /b 1
