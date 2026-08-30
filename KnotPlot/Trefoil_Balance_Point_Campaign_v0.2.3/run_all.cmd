@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ============================================================
echo Trefoil Balance Point Campaign v0.2.3
echo Metric-neutral 100k to 200k boundary/settlement test
echo ============================================================
call run_00_install.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
".venv\Scripts\python.exe" verify_preregistration.py
if errorlevel 1 exit /b %ERRORLEVEL%
call run_05_import_v022.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_10_generate.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_20_probe_100k.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_30_continue_200k.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_40_analyze.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_90_pack_outputs.cmd
exit /b %ERRORLEVEL%
