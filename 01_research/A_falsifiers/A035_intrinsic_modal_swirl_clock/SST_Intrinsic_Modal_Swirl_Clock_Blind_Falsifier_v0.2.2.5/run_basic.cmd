@echo off
setlocal
set OUT=outputs\basic
if exist "%OUT%" rmdir /s /q "%OUT%"
call .venv\Scripts\activate.bat || exit /b 1
echo [1/10] Prepare matched blind selected-library provenance seeds
python -m sst_modal_clock.cli prepare-provenance "%OUT%" config\basic.json %* || exit /b 1
echo [2/10] Stage A nominal: T=24 mesh-stabilized recurrence
python -m sst_modal_clock.cli run "%OUT%" config\basic.json --branch stage_a || exit /b 1
echo [3/10] Analyze Stage A provisional recurrence
python -m sst_modal_clock.cli analyze-stage-a "%OUT%" config\basic.json || exit /b 1
echo [4/10] Mesh-gauge LOW replay on provisional candidates only
python -m sst_modal_clock.cli run "%OUT%" config\basic.json --branch stage_a_gauge_low || exit /b 1
echo [5/10] Mesh-gauge HIGH replay on provisional candidates only
python -m sst_modal_clock.cli run "%OUT%" config\basic.json --branch stage_a_gauge_high || exit /b 1
echo [6/10] Certify Stage A against low/nominal/high mesh gauge
python -m sst_modal_clock.cli analyze-stage-a-gauge "%OUT%" config\basic.json || exit /b 1
echo [7/10] Blind seed-provenance robustness analysis
python -m sst_modal_clock.cli analyze-provenance "%OUT%" config\basic.json || exit /b 1
echo [8/10] Stage B material-core on mesh-gauge-certified candidates only
python -m sst_modal_clock.cli run "%OUT%" config\basic.json --branch material || exit /b 1
echo [9/10] Stage B fixed-core null on same candidates
python -m sst_modal_clock.cli run "%OUT%" config\basic.json --branch fixed || exit /b 1
echo [10/10] Analyze causal/core-specificity Stage B
python -m sst_modal_clock.cli analyze-stage-b "%OUT%" config\basic.json || exit /b 1
echo.
echo Blind Stage-A result:      %OUT%\analysis\blind_stage_a_summary.json
echo Mesh-gauge certification: %OUT%\analysis\blind_stage_a_gauge_summary.json
echo Provenance robustness:     %OUT%\analysis\blind_provenance_summary.json
echo Blind final result:        %OUT%\analysis\blind_summary.json
