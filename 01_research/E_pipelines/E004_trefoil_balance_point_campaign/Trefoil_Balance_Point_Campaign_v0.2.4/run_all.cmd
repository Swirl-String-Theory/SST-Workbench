@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ============================================================
echo Trefoil Balance Point Campaign v0.2.4
echo Overlap-calibrated extended QHP panel to 400k
echo ============================================================
call run_00_install.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
".venv\Scripts\python.exe" verify_preregistration.py
if errorlevel 1 exit /b %ERRORLEVEL%
call run_05_import_v023.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_10_generate.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_20_overlap_to_200k.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_25_verify_overlap.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_30_extension_to_200k.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_35_verify_panel_200k.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_40_continue_400k.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_50_analyze.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_90_pack_outputs.cmd
exit /b %ERRORLEVEL%
