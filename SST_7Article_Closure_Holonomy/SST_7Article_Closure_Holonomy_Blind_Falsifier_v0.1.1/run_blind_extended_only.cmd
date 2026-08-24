@echo off
setlocal
cd /d "%~dp0"
set "DATASET=%~1"
if "%DATASET%"=="" set "DATASET=..\..\KnotPlot\knots\final"
set "RUN=results\extended"
call run_00_install.cmd || goto :fail
if exist "%RUN%" rmdir /s /q "%RUN%"
.venv\Scripts\python.exe scripts\prepare_blind.py --dataset "%DATASET%" --run-dir "%RUN%" --config config/extended.json || goto :fail
.venv\Scripts\python.exe scripts\run_campaign.py --run-dir "%RUN%" --config config/extended.json --mode extended || goto :fail
echo [SST7] EXTENDED BLIND RESULTS FROZEN. Inspect %RUN%\summary_blind.md before reveal.
echo [SST7] Reveal later with: run_reveal.cmd "%RUN%"
exit /b 0
:fail
exit /b 1
