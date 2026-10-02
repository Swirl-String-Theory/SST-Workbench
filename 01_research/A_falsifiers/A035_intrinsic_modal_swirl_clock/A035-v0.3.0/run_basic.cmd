@echo off
setlocal EnableExtensions
set OUT=outputs\basic
rem Do not wipe the whole OUT tree: paper-upgrade stage markers + heartbeat live under outputs\basic.
rem Fresh scientific data only when SST_FRESH=1 or explicit /fresh.
echo.%*| findstr /I /C:"/fresh" >nul && set "SST_FRESH=1"
if /I "%SST_FRESH%"=="1" (
  echo [paper-upgrade] fresh wipe of campaign artifacts under %OUT%
  if exist "%OUT%\prepared" rmdir /s /q "%OUT%\prepared"
  if exist "%OUT%\private" rmdir /s /q "%OUT%\private"
  if exist "%OUT%\analysis" rmdir /s /q "%OUT%\analysis"
  if exist "%OUT%\results_stage_a" rmdir /s /q "%OUT%\results_stage_a"
  if exist "%OUT%\results_stage_a_gauge_low" rmdir /s /q "%OUT%\results_stage_a_gauge_low"
  if exist "%OUT%\results_stage_a_gauge_high" rmdir /s /q "%OUT%\results_stage_a_gauge_high"
  if exist "%OUT%\results_material" rmdir /s /q "%OUT%\results_material"
  if exist "%OUT%\results_fixed" rmdir /s /q "%OUT%\results_fixed"
  del /q "%OUT%\blind_catalog.jsonl" "%OUT%\prepare_summary.json" "%OUT%\run_*_summary.json" 2>nul
)
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
endlocal & exit /b 0
