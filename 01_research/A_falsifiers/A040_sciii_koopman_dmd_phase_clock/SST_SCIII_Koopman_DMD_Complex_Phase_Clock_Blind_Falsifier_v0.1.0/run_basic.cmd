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
echo [3/10] SC-III analysis: discovery complex DMD mode + moving-subspace continuation gates
python -m sst_modal_clock.cli analyze-sciii-stage-a "%OUT%" config\basic.json || exit /b 1
echo [4/10] Mesh-gauge LOW replay on SC-III provisional candidates
python -m sst_modal_clock.cli run "%OUT%" config\basic.json --branch stage_a_gauge_low || exit /b 1
echo [5/10] Mesh-gauge HIGH replay on SC-III provisional candidates
python -m sst_modal_clock.cli run "%OUT%" config\basic.json --branch stage_a_gauge_high || exit /b 1
echo [6/10] SC-III mesh-gauge certification
python -m sst_modal_clock.cli analyze-sciii-gauge "%OUT%" config\basic.json || exit /b 1
echo [7/10] Blind source-family provenance robustness
python -m sst_modal_clock.cli analyze-sciii-provenance "%OUT%" config\basic.json || exit /b 1
echo [8/10] Stage B material-core phase-modulation causality
python -m sst_modal_clock.cli run "%OUT%" config\basic.json --branch material || exit /b 1
echo [9/10] Stage B fixed-core null
python -m sst_modal_clock.cli run "%OUT%" config\basic.json --branch fixed || exit /b 1
echo [10/10] SC-III causal phase-modulation analysis
python -m sst_modal_clock.cli analyze-sciii-stage-b "%OUT%" config\basic.json || exit /b 1
echo.
echo SC-III Stage A: %OUT%\analysis\blind_sciii_stage_a_summary.json
echo SC-III final:   %OUT%\analysis\blind_sciii_summary.json
