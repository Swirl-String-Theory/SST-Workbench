@echo off
setlocal
cd /d "%~dp0"
set "DATASET=%~1"
if "%DATASET%"=="" set "DATASET=..\..\KnotPlot\knots\final"
set "RUN=results\basic"
echo ============================================================
echo SST Seven-Article Closure ^& Holonomy Blind Falsifier v0.1.0
echo Dataset: %DATASET%
echo ============================================================
call run_00_install.cmd || goto :fail
if exist "%RUN%" rmdir /s /q "%RUN%"
.venv\Scripts\python.exe scripts\prepare_blind.py --dataset "%DATASET%" --run-dir "%RUN%" --config config/basic.json || goto :fail
.venv\Scripts\python.exe scripts\run_campaign.py --run-dir "%RUN%" --config config/basic.json --mode basic || goto :fail
.venv\Scripts\python.exe scripts\reveal.py --run-dir "%RUN%" || goto :fail
echo.
echo [SST7] COMPLETE: %RUN%\summary_revealed.md
exit /b 0
:fail
echo [SST7] RUN FAILED
exit /b 1
