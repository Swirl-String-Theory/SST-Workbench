@echo off
setlocal
set DATA=%~1
if "%DATA%"=="" set DATA=..\..\KnotPlot\knots\final
set OUT=outputs\focus_6p3
if exist "%OUT%" rmdir /s /q "%OUT%"
call .venv\Scripts\activate.bat
python -m sst_modal_clock.cli prepare "%DATA%" "%OUT%" config\focus_6p3.json || exit /b 1
python -m sst_modal_clock.cli run "%OUT%" config\focus_6p3.json --branch stage_a || exit /b 1
python -m sst_modal_clock.cli analyze-sciib-stage-a "%OUT%" config\focus_6p3.json || exit /b 1
python -m sst_modal_clock.cli run "%OUT%" config\focus_6p3.json --branch stage_a_gauge_low || exit /b 1
python -m sst_modal_clock.cli run "%OUT%" config\focus_6p3.json --branch stage_a_gauge_high || exit /b 1
python -m sst_modal_clock.cli analyze-sciib-gauge "%OUT%" config\focus_6p3.json || exit /b 1
python -m sst_modal_clock.cli run "%OUT%" config\focus_6p3.json --branch material || exit /b 1
python -m sst_modal_clock.cli run "%OUT%" config\focus_6p3.json --branch fixed || exit /b 1
python -m sst_modal_clock.cli analyze-sciib-stage-b "%OUT%" config\focus_6p3.json || exit /b 1
echo Blind result: %OUT%\analysis\blind_sciib_summary.json
