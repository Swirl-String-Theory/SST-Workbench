@echo off
setlocal
cd /d "%~dp0"
if not defined OMP_NUM_THREADS set "OMP_NUM_THREADS=%NUMBER_OF_PROCESSORS%"
set "INPUT=%~1"
set "OUT=%~2"
echo ============================================================
echo Einstein-SST Emergent Metric + Poisson Gates v0.1.0 [NORMAL]
echo INSTALL - BUILD - SELFTEST - BLIND CAMPAIGN - REVEAL
 echo ============================================================
call run_install.cmd
if errorlevel 1 goto :fail
call run_build_cpp.cmd
if errorlevel 1 goto :fail
call run_selftest.cmd
if errorlevel 1 goto :fail
call run_normal.cmd "%INPUT%" "%OUT%"
if errorlevel 1 goto :fail
echo [SST] DONE. Open outputs\LATEST.txt then REPORT.md
exit /b 0
:fail
echo [SST] ERROR: aborted with code %errorlevel%.
exit /b %errorlevel%
