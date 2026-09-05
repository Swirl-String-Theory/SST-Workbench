@echo off
rem Legacy inherited regression labels only: analyze-stage-a-gauge analyze-provenance
setlocal
set OUT=outputs\basic
if exist "%OUT%" rmdir /s /q "%OUT%"
call .venv\Scripts\activate.bat || exit /b 1
echo [1/10] Prepare blind provenance seeds
python -m sst_modal_clock.cli prepare-provenance "%OUT%" config\basic.json %* || exit /b 1
echo [2/10] Stage A geometry dynamics: T=24
python -m sst_modal_clock.cli run "%OUT%" config\basic.json --branch stage_a || exit /b 1
echo [3/10] SC-IIb analysis: discovery-frozen modal pairs + subspace phase gates
python -m sst_modal_clock.cli analyze-sciib-stage-a "%OUT%" config\basic.json || exit /b 1
echo [4/10] Mesh-gauge LOW replay on SC-IIb provisional candidates
python -m sst_modal_clock.cli run "%OUT%" config\basic.json --branch stage_a_gauge_low || exit /b 1
echo [5/10] Mesh-gauge HIGH replay on SC-IIb provisional candidates
python -m sst_modal_clock.cli run "%OUT%" config\basic.json --branch stage_a_gauge_high || exit /b 1
echo [6/10] SC-IIb mesh-gauge certification
python -m sst_modal_clock.cli analyze-sciib-gauge "%OUT%" config\basic.json || exit /b 1
echo [7/10] Blind source-family provenance robustness
python -m sst_modal_clock.cli analyze-sciib-provenance "%OUT%" config\basic.json || exit /b 1
echo [8/10] Stage B material-core phase-modulation causality
python -m sst_modal_clock.cli run "%OUT%" config\basic.json --branch material || exit /b 1
echo [9/10] Stage B fixed-core null
python -m sst_modal_clock.cli run "%OUT%" config\basic.json --branch fixed || exit /b 1
echo [10/10] SC-IIb causal phase-modulation analysis
python -m sst_modal_clock.cli analyze-sciib-stage-b "%OUT%" config\basic.json || exit /b 1
echo.
echo SC-IIb Stage A: %OUT%\analysis\blind_sciib_stage_a_summary.json
echo SC-IIb final:   %OUT%\analysis\blind_sciib_summary.json
