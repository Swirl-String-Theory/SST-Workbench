@echo off
setlocal
cd /d "%~dp0"
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set STAMP=%%i
set OUT=outputs\basic_%STAMP%
echo ============================================================
echo SST Chirality-Helicity Transport Polarity Falsifier v0.1.0
echo BASIC BLIND CHAIN
echo Dataset: ..\..\KnotPlot\knots\final
echo Output : %OUT%
echo ============================================================
call run_00_setup.cmd || exit /b 1
call run_01_build_native.cmd || exit /b 1
call run_05_selftest.cmd || exit /b 1
call run_campaign.cmd configs\basic.json "%OUT%" || exit /b 1
echo.
echo ============================================================
echo BLIND RESULT READY
echo %OUT%\REPORT_BLIND.md
echo ============================================================
echo Do not reveal until you have inspected/saved the blind report.
echo Then run:
echo   run_40_reveal.cmd "%OUT%"
exit /b 0
