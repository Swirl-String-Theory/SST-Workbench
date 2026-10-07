@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
set "WB=%~1"
if "!WB!"=="" if defined SST_WORKBENCH_ROOT set "WB=!SST_WORKBENCH_ROOT!"
if "!WB!"=="" set "WB=C:\workspace\projects\SST-Workbench"
if not exist "!WB!" (echo [ERROR] SST-Workbench root not found: !WB! & exit /b 2)
echo [INFO] SST-Workbench root: !WB!
call run_00_install.cmd || exit /b !errorlevel!
call run_01_selftest.cmd || exit /b !errorlevel!
set "PY=%CD%\.venv\Scripts\python.exe"
for /f %%i in ('"%PY%" tools\timestamp.py') do set "TS=%%i"
set "OUT=A054_Nucleon_Topology_Architecture_Blind_Falsifier_v0.2.0-outputs\basic_!TS!"
call run_02_prepare_cert.cmd "!WB!" "!OUT!" basic || exit /b !errorlevel!
call run_03_certify.cmd "!OUT!" basic || exit /b !errorlevel!
call run_90_pack_blind.cmd "!OUT!" || exit /b !errorlevel!
echo.
echo STOPPED BEFORE REVEAL by design.
exit /b 0
