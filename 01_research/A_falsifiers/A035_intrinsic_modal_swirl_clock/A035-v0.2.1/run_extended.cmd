@echo off
setlocal
set DATA=%~1
if "%DATA%"=="" set DATA=..\..\KnotPlot\knots\final
set OUT=outputs\extended
if exist "%OUT%" rmdir /s /q "%OUT%"
call .venv\Scripts\activate.bat
echo [1/9] Prepare blind +/-/0 probes EXTENDED
python -m sst_modal_clock.cli prepare "%DATA%" "%OUT%" config\extended.json || exit /b 1
echo [2/9] Stage A nominal EXTENDED: T=36
python -m sst_modal_clock.cli run "%OUT%" config\extended.json --branch stage_a || exit /b 1
echo [3/9] Analyze Stage A provisional recurrence
python -m sst_modal_clock.cli analyze-stage-a "%OUT%" config\extended.json || exit /b 1
echo [4/9] Mesh-gauge LOW replay
python -m sst_modal_clock.cli run "%OUT%" config\extended.json --branch stage_a_gauge_low || exit /b 1
echo [5/9] Mesh-gauge HIGH replay
python -m sst_modal_clock.cli run "%OUT%" config\extended.json --branch stage_a_gauge_high || exit /b 1
echo [6/9] Mesh-gauge certification
python -m sst_modal_clock.cli analyze-stage-a-gauge "%OUT%" config\extended.json || exit /b 1
echo [7/9] Stage B material-core on certified candidates only
python -m sst_modal_clock.cli run "%OUT%" config\extended.json --branch material || exit /b 1
echo [8/9] Stage B fixed-core null
python -m sst_modal_clock.cli run "%OUT%" config\extended.json --branch fixed || exit /b 1
echo [9/9] Analyze Stage B
python -m sst_modal_clock.cli analyze-stage-b "%OUT%" config\extended.json || exit /b 1
