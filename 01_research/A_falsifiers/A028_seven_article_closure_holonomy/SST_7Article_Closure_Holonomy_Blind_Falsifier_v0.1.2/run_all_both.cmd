@echo off
setlocal
cd /d "%~dp0"
set "DATASET=%~1"
if "%DATASET%"=="" set "DATASET=..\..\KnotPlot\knots\final"
set "BASIC=results\basic"
set "EXT=results\extended"
echo ============================================================
echo SST7 v0.1.2 BASIC + EXTENDED with shared blind manifest
echo Dataset: %DATASET%
echo ============================================================
call run_00_install.cmd || goto :fail
if exist "%BASIC%" rmdir /s /q "%BASIC%"
if exist "%EXT%" rmdir /s /q "%EXT%"
.venv\Scripts\python.exe scripts\prepare_blind.py --dataset "%DATASET%" --run-dir "%BASIC%" --config config/basic.json --shared-state-dir results\_blind_state || goto :fail
.venv\Scripts\python.exe scripts\run_campaign.py --run-dir "%BASIC%" --config config/basic.json --mode basic || goto :fail
.venv\Scripts\python.exe scripts\reveal.py --run-dir "%BASIC%" || goto :fail
.venv\Scripts\python.exe scripts\prepare_blind.py --dataset "%DATASET%" --run-dir "%EXT%" --config config/extended.json --shared-state-dir results\_blind_state || goto :fail
.venv\Scripts\python.exe scripts\run_campaign.py --run-dir "%EXT%" --config config/extended.json --mode extended || goto :fail
.venv\Scripts\python.exe scripts\reveal.py --run-dir "%EXT%" || goto :fail
.venv\Scripts\python.exe scripts\compare_manifests.py --a "%BASIC%" --b "%EXT%" || goto :fail
echo [SST7] BOTH RUNS COMPLETE AND MANIFESTS MATCH.
exit /b 0
:fail
echo [SST7] BASIC+EXTENDED RUN FAILED
exit /b 1
