@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo SST Quantum Galileo Action-Gauge Closure Falsifier v0.1.0
echo FULL blind -> reveal chain
echo ============================================================
call run_01_install.cmd
if errorlevel 1 exit /b 1
call run_02_build_native.cmd
if errorlevel 1 exit /b 1
call run_03_tests.cmd
if errorlevel 1 exit /b 1
echo ============================================================
echo [4/7] Blind prepare
echo ============================================================
call run_prepare_blind.cmd
if errorlevel 1 exit /b 1
echo ============================================================
echo [5/7] BASIC
echo ============================================================
call run_basic.cmd
if errorlevel 1 exit /b 1
echo ============================================================
echo [6/7] EXTENDED
echo ============================================================
call run_extended.cmd
if errorlevel 1 exit /b 1
echo ============================================================
echo [7/7] Reveal + package
echo ============================================================
call run_reveal.cmd
if errorlevel 1 exit /b 1
echo.
echo ============================================================
echo COMPLETE
echo ============================================================
echo Results:
echo   .\SST_Quantum_Galileo_Action_Gauge_Closure_Falsifier_v0.1.0-outputs\
echo Archives:
echo   ..\SST_Quantum_Galileo_Action_Gauge_Closure_Falsifier_v0.1.0-outputs_BLIND.zip
echo   ..\SST_Quantum_Galileo_Action_Gauge_Closure_Falsifier_v0.1.0-outputs_REVEALED.zip
endlocal
