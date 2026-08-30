@echo off
setlocal
set OUT=outputs\links_basic
if exist "%OUT%" rmdir /s /q "%OUT%"
echo ============================================================
echo SST Modal Clock v0.2.2.6 - LINK-ONLY provenance campaign
echo Default: Gilbert + Katlas, minimum 2 independent source-family carriers
echo Extra CLI arguments are appended and may override defaults.
echo ============================================================
call run_setup.cmd || exit /b 1
call run_build_native.cmd || exit /b 1
call run_selftest.cmd || exit /b 1
call .venv\Scripts\activate.bat || exit /b 1
python -m sst_modal_clock.cli scan-provenance config\basic.json --libraries=Gilbert,Katlas --min-carriers=2 --kind=links %* > outputs\SOURCE_SCAN_LINKS.json || exit /b 1
python -m sst_modal_clock.cli prepare-provenance "%OUT%" config\basic.json --libraries=Gilbert,Katlas --min-carriers=2 --kind=links %* || exit /b 1
python -m sst_modal_clock.cli run "%OUT%" config\basic.json --branch stage_a || exit /b 1
python -m sst_modal_clock.cli analyze-stage-a "%OUT%" config\basic.json || exit /b 1
python -m sst_modal_clock.cli run "%OUT%" config\basic.json --branch stage_a_gauge_low || exit /b 1
python -m sst_modal_clock.cli run "%OUT%" config\basic.json --branch stage_a_gauge_high || exit /b 1
python -m sst_modal_clock.cli analyze-stage-a-gauge "%OUT%" config\basic.json || exit /b 1
python -m sst_modal_clock.cli analyze-provenance "%OUT%" config\basic.json || exit /b 1
python -m sst_modal_clock.cli run "%OUT%" config\basic.json --branch material || exit /b 1
python -m sst_modal_clock.cli run "%OUT%" config\basic.json --branch fixed || exit /b 1
python -m sst_modal_clock.cli analyze-stage-b "%OUT%" config\basic.json || exit /b 1
echo.
echo Link source scan: outputs\SOURCE_SCAN_LINKS.json
echo Blind result:     %OUT%\analysis\blind_summary.json
