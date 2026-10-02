@echo off
setlocal
set DATA=%~1
if "%DATA%"=="" set DATA=..\..\KnotPlot\knots\final
set OUT=outputs\basic
if exist "%OUT%" rmdir /s /q "%OUT%"
call .venv\Scripts\activate.bat
echo [1/6] Prepare blind +/-/0 probes
python -m sst_modal_clock.cli prepare "%DATA%" "%OUT%" config\basic.json || exit /b 1
echo [2/6] Stage A: long geometry-only mesh-stabilized recurrence
python -m sst_modal_clock.cli run "%OUT%" config\basic.json --branch stage_a || exit /b 1
echo [3/6] Analyze Stage A with frozen early POD modes
python -m sst_modal_clock.cli analyze-stage-a "%OUT%" config\basic.json || exit /b 1
echo [4/6] Stage B material-core on Stage-A candidates only
python -m sst_modal_clock.cli run "%OUT%" config\basic.json --branch material || exit /b 1
echo [5/6] Stage B fixed-core null on same candidates
python -m sst_modal_clock.cli run "%OUT%" config\basic.json --branch fixed || exit /b 1
echo [6/6] Analyze causal/core-specificity Stage B
python -m sst_modal_clock.cli analyze-stage-b "%OUT%" config\basic.json || exit /b 1
echo Blind Stage-A result: %OUT%\analysis\blind_stage_a_summary.json
echo Blind final result:   %OUT%\analysis\blind_summary.json
