@echo off
setlocal
set OUT=outputs\extended
if exist "%OUT%" rmdir /s /q "%OUT%"
call .venv\Scripts\activate.bat || exit /b 1
echo [1/10] Prepare matched provenance seeds EXTENDED
python -m sst_modal_clock.cli prepare-provenance "%OUT%" config\extended.json %* || exit /b 1
echo [2/10] Stage A nominal EXTENDED
python -m sst_modal_clock.cli run "%OUT%" config\extended.json --branch stage_a || exit /b 1
echo [3/10] Analyze Stage A
python -m sst_modal_clock.cli analyze-sciib-stage-a "%OUT%" config\extended.json || exit /b 1
echo [4/10] Mesh-gauge LOW replay
python -m sst_modal_clock.cli run "%OUT%" config\extended.json --branch stage_a_gauge_low || exit /b 1
echo [5/10] Mesh-gauge HIGH replay
python -m sst_modal_clock.cli run "%OUT%" config\extended.json --branch stage_a_gauge_high || exit /b 1
echo [6/10] Mesh-gauge certification
python -m sst_modal_clock.cli analyze-sciib-gauge "%OUT%" config\extended.json || exit /b 1
echo [7/10] Seed-provenance robustness
python -m sst_modal_clock.cli analyze-sciib-provenance "%OUT%" config\extended.json || exit /b 1
echo [8/10] Stage B material
python -m sst_modal_clock.cli run "%OUT%" config\extended.json --branch material || exit /b 1
echo [9/10] Stage B fixed
python -m sst_modal_clock.cli run "%OUT%" config\extended.json --branch fixed || exit /b 1
echo [10/10] Stage B analysis
python -m sst_modal_clock.cli analyze-sciib-stage-b "%OUT%" config\extended.json || exit /b 1
