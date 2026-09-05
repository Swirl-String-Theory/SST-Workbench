@echo off
setlocal
set DATA=%~1
if "%DATA%"=="" set DATA=..\..\KnotPlot\knots\final
set OUT=outputs\extended
if exist "%OUT%" rmdir /s /q "%OUT%"
call .venv\Scripts\activate.bat
echo [1/6] Prepare blind +/-/0 probes
python -m sst_modal_clock.cli prepare "%DATA%" "%OUT%" config\extended.json || exit /b 1
echo [2/6] Stage A EXTENDED long recurrence
python -m sst_modal_clock.cli run "%OUT%" config\extended.json --branch stage_a || exit /b 1
echo [3/6] Analyze Stage A
python -m sst_modal_clock.cli analyze-stage-a "%OUT%" config\extended.json || exit /b 1
echo [4/6] Stage B material-core candidates only
python -m sst_modal_clock.cli run "%OUT%" config\extended.json --branch material || exit /b 1
echo [5/6] Stage B fixed-core null
python -m sst_modal_clock.cli run "%OUT%" config\extended.json --branch fixed || exit /b 1
echo [6/6] Analyze Stage B
python -m sst_modal_clock.cli analyze-stage-b "%OUT%" config\extended.json || exit /b 1
echo Blind Stage-A result: %OUT%\analysis\blind_stage_a_summary.json
echo Blind final result:   %OUT%\analysis\blind_summary.json
