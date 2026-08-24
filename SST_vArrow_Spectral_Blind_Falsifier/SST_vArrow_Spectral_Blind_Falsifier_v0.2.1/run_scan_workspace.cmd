@echo off
setlocal EnableExtensions
cd /d "%~dp0" || exit /b 1

rem Package layout expected by the SST Workbench:
rem   SST-Workbench\SST_vArrow_Spectral_Blind_Falsifier\SST_vArrow_..._v0.2.1
rem Therefore ..\.. is normally the SST-Workbench root.
set "WORKSPACE=%~1"
if not defined WORKSPACE set "WORKSPACE=..\.."
set "OUTDIR=%~2"
if not defined OUTDIR set "OUTDIR=outputs_workspace_scan"

echo ============================================================
echo SST v-arrow v0.2.1 - workspace recursive discovery
for %%I in ("%WORKSPACE%") do echo Workspace root: %%~fI
echo Output: %OUTDIR%
echo ============================================================

call "%~dp0run_scan.cmd" "%WORKSPACE%" "%OUTDIR%"
set "RC=%ERRORLEVEL%"
endlocal & exit /b %RC%
