@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
set WB=C:\workspace\projects\SST-Workbench
call run_00_install.cmd || exit /b !errorlevel!
call run_01_selftest.cmd || exit /b !errorlevel!
for /f %%i in ('python tools\timestamp.py') do set "TS=%%i"
set "OUT=A054_Nucleon_Topology_Architecture_Blind_Falsifier_v0.2.0-outputs\full_!TS!"
call run_02_prepare_cert.cmd "%WB%" "!OUT!" full || exit /b !errorlevel!
call run_03_certify.cmd "!OUT!" full || exit /b !errorlevel!
call run_90_pack_blind.cmd "!OUT!" || exit /b !errorlevel!
echo STOPPED BEFORE REVEAL by design.
exit /b 0