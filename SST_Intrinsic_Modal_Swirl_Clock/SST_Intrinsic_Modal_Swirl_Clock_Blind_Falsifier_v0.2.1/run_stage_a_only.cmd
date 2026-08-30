@echo off
setlocal
set DATA=%~1
if "%DATA%"=="" set DATA=..\..\KnotPlot\knots\final
set OUT=outputs\stage_a_only
if exist "%OUT%" rmdir /s /q "%OUT%"
call .venv\Scripts\activate.bat
python -m sst_modal_clock.cli prepare "%DATA%" "%OUT%" config\basic.json || exit /b 1
python -m sst_modal_clock.cli run "%OUT%" config\basic.json --branch stage_a || exit /b 1
python -m sst_modal_clock.cli analyze-stage-a "%OUT%" config\basic.json || exit /b 1
python -m sst_modal_clock.cli run "%OUT%" config\basic.json --branch stage_a_gauge_low || exit /b 1
python -m sst_modal_clock.cli run "%OUT%" config\basic.json --branch stage_a_gauge_high || exit /b 1
python -m sst_modal_clock.cli analyze-stage-a-gauge "%OUT%" config\basic.json || exit /b 1
echo Stage-A summary: %OUT%\analysis\blind_stage_a_summary.json
echo Gauge summary:   %OUT%\analysis\blind_stage_a_gauge_summary.json
