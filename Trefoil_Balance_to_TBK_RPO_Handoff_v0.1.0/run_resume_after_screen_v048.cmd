@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ============================================================
echo Trefoil Balance to TBK/RPO v0.4.8 resume after FP64 screen
echo Reuses existing screen; does not rerun the 8 screen datasets.
echo ============================================================

call run_00_install.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_01_verify_preanalysis_lock.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_02_preflight_v048.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_05_prepare_handoff.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_06_verify_selection_lock.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_07_verify_existing_screen.cmd
if errorlevel 1 (
    echo Existing screen does not match the current locked selected set.
    echo Run run_all_v048.cmd instead.
    exit /b 7
)

call run_20_spectral_v048_auto.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_30_confirm_v048_fp64.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_40_summarize.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_90_pack_outputs.cmd
exit /b %ERRORLEVEL%
