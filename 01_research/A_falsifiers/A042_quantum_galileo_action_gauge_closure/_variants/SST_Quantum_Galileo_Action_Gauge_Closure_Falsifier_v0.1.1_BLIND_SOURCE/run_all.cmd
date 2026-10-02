@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo SST Quantum Galileo Action-Gauge Closure Falsifier v0.1.1
echo STRICT BLIND CHAIN
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
echo [5/7] BASIC action-domain gates
echo ============================================================
call run_basic.cmd
if errorlevel 1 exit /b 1
echo ============================================================
echo [6/7] EXTENDED action-domain gates
echo ============================================================
call run_extended.cmd
if errorlevel 1 exit /b 1
echo ============================================================
echo [7/7] Seal BLIND archive
echo ============================================================
call run_package.cmd
if errorlevel 1 exit /b 1
echo.
echo ============================================================
echo BLIND RUN COMPLETE
echo ============================================================
echo Blind archive:
echo   ..\SST_Quantum_Galileo_Action_Gauge_Closure_Falsifier_v0.1.1-outputs_BLIND.zip
echo.
echo Only NOW extract the separate REVEAL_KEY archive into this project.
echo Then run:
echo   run_reveal.cmd
endlocal
