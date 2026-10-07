@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
call run_00_install.cmd || exit /b !errorlevel!
call run_01_selftest.cmd || exit /b !errorlevel!
for /f %%i in ('python tools\timestamp.py') do set "TS=%%i"
set "OUT=A054_Nucleon_Topology_Architecture_Blind_Falsifier_v0.1.1-r1-outputs\controls_!TS!"
call run_02_prepare_blind.cmd "%~1" "!OUT!" || exit /b !errorlevel!
call run_03_blind.cmd "!OUT!" || exit /b !errorlevel!
echo.
echo CONTROL/DIAGNOSTIC run complete. PREPARED_FULL is NOT required here.
exit /b 0
