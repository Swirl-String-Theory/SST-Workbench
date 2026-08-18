@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "THREADS=%~1"
if "%THREADS%"=="" set "THREADS=16"
set "KNOTS=%~2"
echo ============================================================
echo Kelvin-Kirchhoff SST Falsifier v0.1.1
echo Install -^> native selftest -^> basic blind run -^> extended blind run
echo Threads: %THREADS%
echo ============================================================
call run_00_install.cmd
if errorlevel 1 exit /b 1
call run_01_selftest.cmd %THREADS%
if errorlevel 1 exit /b 1
if "%KNOTS%"=="" (
  call run_10_basic.cmd %THREADS%
) else (
  call run_10_basic.cmd %THREADS% "%KNOTS%"
)
if errorlevel 1 exit /b 1
if "%KNOTS%"=="" (
  call run_20_extended.cmd %THREADS%
) else (
  call run_20_extended.cmd %THREADS% "%KNOTS%"
)
if errorlevel 1 exit /b 1
echo ============================================================
echo [KK-SST] ALL PASS: pipeline completed through extended campaign.
echo Inspect newest outputs_extended_*\REPORT.md and unblinded_summary.csv
echo ============================================================
endlocal
