@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ============================================================
echo Trefoil v0.2.4.2 incomplete-continuation recovery
echo Reuses all completed settings; does NOT rerun cold-start stages
echo ============================================================
if "%QHP_PROGRESS_EVERY%"=="" set QHP_PROGRESS_EVERY=15
if exist ".venv\Scripts\python.exe" (set PYEXE=.venv\Scripts\python.exe) else (echo ERROR: .venv missing. Run run_00_install.cmd once. & exit /b 2)
%PYEXE% check_continuation_completeness.py
if errorlevel 1 exit /b %ERRORLEVEL%
%PYEXE% run_campaign.py --stage continuation --progress-every=%QHP_PROGRESS_EVERY%
if errorlevel 1 exit /b %ERRORLEVEL%
%PYEXE% check_continuation_completeness.py --require-complete
if errorlevel 1 exit /b %ERRORLEVEL%
set PYTHONUTF8=1
%PYEXE% analyze.py
if errorlevel 1 exit /b %ERRORLEVEL%
call run_90_pack_outputs.cmd
exit /b %ERRORLEVEL%
