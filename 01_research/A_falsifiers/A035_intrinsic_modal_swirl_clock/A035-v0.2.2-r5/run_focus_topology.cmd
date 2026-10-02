@echo off
setlocal EnableExtensions
if "%~1"=="" (
  echo Usage: run_focus_topology.cmd ^<topology^> [--libraries=...] [--min-carriers=N] [--kind=knots^|links]
  echo Example: run_focus_topology.cmd L2a1 --libraries=Gilbert,Katlas --min-carriers=2 --kind=links
  exit /b 2
)
set TOPOLOGY=%~1
shift
set "EXTRA="
:collect_args
if "%~1"=="" goto args_done
set "EXTRA=%EXTRA% %~1"
shift
goto collect_args
:args_done
set OUT=outputs\focus_%TOPOLOGY%
if exist "%OUT%" rmdir /s /q "%OUT%"
echo ============================================================
echo SST Modal Clock v0.2.2.6 - topology focus: %TOPOLOGY%
echo ============================================================
call run_setup.cmd || exit /b 1
call run_build_native.cmd || exit /b 1
call run_selftest.cmd || exit /b 1
call .venv\Scripts\activate.bat || exit /b 1
python -m sst_modal_clock.cli scan-provenance config\basic.json --topology=%TOPOLOGY% %EXTRA% > "outputs\SOURCE_SCAN_%TOPOLOGY%.json" || exit /b 1
python -m sst_modal_clock.cli prepare-provenance "%OUT%" config\basic.json --topology=%TOPOLOGY% %EXTRA% || exit /b 1
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
echo Source scan: outputs\SOURCE_SCAN_%TOPOLOGY%.json
echo Blind result: %OUT%\analysis\blind_summary.json
