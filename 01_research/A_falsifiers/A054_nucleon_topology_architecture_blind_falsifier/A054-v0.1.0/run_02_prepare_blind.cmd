@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
call .venv\Scripts\activate.bat
set "WB=%~1"
if "!WB!"=="" if defined SST_WORKBENCH_ROOT set "WB=!SST_WORKBENCH_ROOT!"
if "!WB!"=="" set "WB=C:\workspace\projects\SST-Workbench"
set "OUT=%~2"
if "!OUT!"=="" (
  for /f %%i in ('python tools\timestamp.py') do set "TS=%%i"
  set "OUT=A054_Nucleon_Topology_Architecture_Blind_Falsifier_v0.1.0-outputs\basic_!TS!"
)
a054-ntaf prepare --workbench "!WB!" --output "!OUT!" --n 144
if errorlevel 1 exit /b !errorlevel!
python tools\build_blind_runner.py --campaign "!OUT!" || exit /b !errorlevel!
echo !OUT!>LAST_CAMPAIGN.txt
echo Prepared: !OUT!
exit /b 0
