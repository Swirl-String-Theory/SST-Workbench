@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo SST Quantum Galileo Action-Gauge Closure Falsifier v0.2.0
echo PROVENANCE-CLEAN GEOMETRY/FLUID -> ACTION QUANTUM
echo STRICT BLIND CHAIN
echo ============================================================

call run_01_install.cmd
if errorlevel 1 exit /b 1

call run_02_build_native.cmd
if errorlevel 1 exit /b 1

call run_03_tests.cmd
if errorlevel 1 exit /b 1

echo ============================================================
echo [4/9] Blind geometry prepare
echo ============================================================
call run_prepare_blind.cmd
if errorlevel 1 exit /b 1

echo ============================================================
echo [5/9] QGI raw phase / public-data preparation
echo ============================================================
call run_prepare_qgi_phase.cmd
if errorlevel 1 exit /b 1

echo ============================================================
echo [6/9] Provenance-clean fluid circulation preparation
echo ============================================================
call run_prepare_fluid_action.cmd
if errorlevel 1 exit /b 1

echo ============================================================
echo [7/9] BASIC
echo ============================================================
call run_basic.cmd
if errorlevel 1 exit /b 1

echo ============================================================
echo [8/9] EXTENDED
echo ============================================================
call run_extended.cmd
if errorlevel 1 exit /b 1

echo ============================================================
echo [9/9] Seal BLIND archive
echo ============================================================
call run_package.cmd
if errorlevel 1 exit /b 1

echo.
echo ============================================================
echo BLIND RUN COMPLETE
echo ============================================================
echo Blind archive:
echo   ..\SST_Quantum_Galileo_Action_Gauge_Closure_Falsifier_v0.2.0-outputs_BLIND.zip
echo.
echo Only now extract the separate REVEAL_KEY archive and run:
echo   run_reveal.cmd
endlocal
