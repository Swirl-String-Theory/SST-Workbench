@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ============================================================
echo Trefoil Balance to TBK/RPO v0.4.6 fallback
echo selected blind set : FULL CPU/OpenMP FP64
echo ============================================================
call run_00_install.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_01_verify_preanalysis_lock.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_02_preflight_v046.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_05_prepare_handoff.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_06_verify_selection_lock.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_35_full_v046_fp64.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_40_summarize.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_90_pack_outputs.cmd
exit /b %ERRORLEVEL%
