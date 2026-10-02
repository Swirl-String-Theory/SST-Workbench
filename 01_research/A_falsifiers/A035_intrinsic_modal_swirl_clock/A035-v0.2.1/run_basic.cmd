@echo off
setlocal
set DATA=%~1
if "%DATA%"=="" set DATA=..\..\KnotPlot\knots\final
set OUT=outputs\basic
if exist "%OUT%" rmdir /s /q "%OUT%"
call .venv\Scripts\activate.bat
echo [1/9] Prepare blind +/-/0 probes
python -m sst_modal_clock.cli prepare "%DATA%" "%OUT%" config\basic.json || exit /b 1
echo [2/9] Stage A nominal: T=24 mesh-stabilized recurrence
python -m sst_modal_clock.cli run "%OUT%" config\basic.json --branch stage_a || exit /b 1
echo [3/9] Analyze Stage A provisional recurrence with parameterization-invariant POD
python -m sst_modal_clock.cli analyze-stage-a "%OUT%" config\basic.json || exit /b 1
echo [4/9] Mesh-gauge LOW replay on provisional candidates only
python -m sst_modal_clock.cli run "%OUT%" config\basic.json --branch stage_a_gauge_low || exit /b 1
echo [5/9] Mesh-gauge HIGH replay on provisional candidates only
python -m sst_modal_clock.cli run "%OUT%" config\basic.json --branch stage_a_gauge_high || exit /b 1
echo [6/9] Certify Stage A candidates against mesh-gauge variation
python -m sst_modal_clock.cli analyze-stage-a-gauge "%OUT%" config\basic.json || exit /b 1
echo [7/9] Stage B material-core on mesh-gauge-certified candidates only
python -m sst_modal_clock.cli run "%OUT%" config\basic.json --branch material || exit /b 1
echo [8/9] Stage B fixed-core null on same candidates
python -m sst_modal_clock.cli run "%OUT%" config\basic.json --branch fixed || exit /b 1
echo [9/9] Analyze causal/core-specificity Stage B
python -m sst_modal_clock.cli analyze-stage-b "%OUT%" config\basic.json || exit /b 1
echo Blind Stage-A result:       %OUT%\analysis\blind_stage_a_summary.json
echo Mesh-gauge certification:  %OUT%\analysis\blind_stage_a_gauge_summary.json
echo Blind final result:         %OUT%\analysis\blind_summary.json
