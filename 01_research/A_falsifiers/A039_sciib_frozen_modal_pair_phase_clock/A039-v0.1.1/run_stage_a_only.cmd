@echo off
setlocal
set OUT=outputs\stage_a_only
if exist "%OUT%" rmdir /s /q "%OUT%"
call .venv\Scripts\activate.bat || exit /b 1
python -m sst_modal_clock.cli prepare-provenance "%OUT%" config\basic.json %* || exit /b 1
python -m sst_modal_clock.cli run "%OUT%" config\basic.json --branch stage_a || exit /b 1
python -m sst_modal_clock.cli analyze-sciib-stage-a "%OUT%" config\basic.json || exit /b 1
python -m sst_modal_clock.cli run "%OUT%" config\basic.json --branch stage_a_gauge_low || exit /b 1
python -m sst_modal_clock.cli run "%OUT%" config\basic.json --branch stage_a_gauge_high || exit /b 1
python -m sst_modal_clock.cli analyze-sciib-gauge "%OUT%" config\basic.json || exit /b 1
python -m sst_modal_clock.cli analyze-sciib-provenance "%OUT%" config\basic.json || exit /b 1
echo Stage-A summary:  %OUT%\analysis\blind_stage_a_summary.json
echo Gauge summary:    %OUT%\analysis\blind_stage_a_gauge_summary.json
echo Provenance:       %OUT%\analysis\blind_sciib_provenance_summary.json
