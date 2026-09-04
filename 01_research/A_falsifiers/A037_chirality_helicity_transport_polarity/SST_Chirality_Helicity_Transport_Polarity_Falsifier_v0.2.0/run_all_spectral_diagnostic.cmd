@echo off
setlocal
cd /d "%~dp0"
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set STAMP=%%i
set OUT=outputs\spectral_%STAMP%
call run_00_setup.cmd || exit /b 1
call run_01_build_native.cmd || exit /b 1
call run_05_selftest.cmd || exit /b 1
call run_campaign.cmd configs\spectral_diagnostic.json "%OUT%" || exit /b 1
echo Blind spectral diagnostic: %OUT%\REPORT_BLIND.md
echo Reveal: run_40_reveal.cmd "%OUT%"
exit /b 0
