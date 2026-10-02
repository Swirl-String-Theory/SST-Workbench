@echo off
setlocal
cd /d "%~dp0"
set "DATASET=%~1"
if "%DATASET%"=="" set "DATASET=..\..\KnotPlot\knots\final"
echo ============================================================
echo SST Material-Coordinate / Phase-Shift EFT Falsifier v0.1.0
echo One-click chain
echo Dataset: %DATASET%
echo ============================================================
echo [1/3] Setup
call run_setup.cmd
if errorlevel 1 exit /b 1
echo [2/3] Basic
call run_basic.cmd "%DATASET%" "outputs\basic"
if errorlevel 1 exit /b 1
echo [3/3] Extended
call run_extended.cmd "%DATASET%" "outputs\extended"
if errorlevel 1 exit /b 1
echo ============================================================
echo DONE
echo Basic   : outputs\basic\REPORT.md
echo Extended: outputs\extended\REPORT.md
echo ============================================================
endlocal
