@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
call run_00_install.cmd || exit /b !errorlevel!
call .venv\Scripts\activate.bat
python -c "from a054_ntaf import _native; assert _native.openmp_enabled; print('native OpenMP: PASS')" || (echo Extended requires C++/OpenMP. & exit /b 3)
call run_01_selftest.cmd || exit /b !errorlevel!
set "WB=%~1"
if "!WB!"=="" if defined SST_WORKBENCH_ROOT set "WB=!SST_WORKBENCH_ROOT!"
if "!WB!"=="" set "WB=C:\workspace\projects\SST-Workbench"
for /f %%i in ('python tools\timestamp.py') do set "TS=%%i"
set "OUT=A054_Nucleon_Topology_Architecture_Blind_Falsifier_v0.1.1-outputs\extended_!TS!"
a054-ntaf prepare --workbench "!WB!" --output "!OUT!" --n 192 || exit /b !errorlevel!
python tools\build_blind_runner.py --campaign "!OUT!" || exit /b !errorlevel!
python "!OUT!\blind_runner\run_blind.py" --campaign "!OUT!" --config configs\extended.json || exit /b !errorlevel!
echo !OUT!>LAST_CAMPAIGN.txt
echo STOPPED BEFORE REVEAL by design.
exit /b 0
