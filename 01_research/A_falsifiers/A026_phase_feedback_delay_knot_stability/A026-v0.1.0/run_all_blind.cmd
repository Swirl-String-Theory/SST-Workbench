@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo [0/5] Resolve final-checkpoint dataset
call "_RESOLVE_INPUT.cmd" "%~1" || goto :fail
set "PRESET=%~2"
if "%PRESET%"=="" set "PRESET=basic"
call run_00_install.cmd || goto :fail
call run_10_prepare_blind.cmd "%INPUT%" "%PRESET%" || goto :fail
call run_20_delay_predict.cmd "%PRESET%" || goto :fail
call run_30_nonlinear_measure.cmd "%PRESET%" || goto :fail
call run_35_freeze_and_evaluate.cmd
set RC=%ERRORLEVEL%
echo ============================================================
echo BLIND RUN COMPLETE. Results are frozen. Reveal has NOT run.
echo Primary result: results\BLIND_EVALUATION.json
echo Reveal key hash: blind_work\reveal_key_sha256.txt
echo ============================================================
exit /b %RC%
:fail
echo FAILED before blind freeze.
exit /b 1
