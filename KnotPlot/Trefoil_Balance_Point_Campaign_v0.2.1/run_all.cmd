@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ============================================================
echo Trefoil Balance Point Campaign v0.2.1 : K31 qhp sweep to 30000
echo ============================================================
call run_00_install.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_02_verify_preregistration.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_05_generate.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_10_validate_syntax.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_30_campaign.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_40_analyze.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_90_pack_outputs.cmd
exit /b %ERRORLEVEL%
