@echo off
setlocal
set DATA=%~1
if "%DATA%"=="" set DATA=..\..\KnotPlot\knots\final
call .venv\Scripts\activate.bat
for %%N in (64 96 128) do (
  if exist "outputs\resolution_N%%N" rmdir /s /q "outputs\resolution_N%%N"
  echo [N=%%N] prepare
  python -m sst_modal_clock.cli prepare "%DATA%" "outputs\resolution_N%%N" "config\resolution_N%%N.json" || exit /b 1
  echo [N=%%N] Stage A nominal
  python -m sst_modal_clock.cli run "outputs\resolution_N%%N" "config\resolution_N%%N.json" --branch stage_a || exit /b 1
  python -m sst_modal_clock.cli analyze-sciii-stage-a "outputs\resolution_N%%N" "config\resolution_N%%N.json" || exit /b 1
  echo [N=%%N] mesh-gauge certification on provisional candidates
  python -m sst_modal_clock.cli run "outputs\resolution_N%%N" "config\resolution_N%%N.json" --branch stage_a_gauge_low || exit /b 1
  python -m sst_modal_clock.cli run "outputs\resolution_N%%N" "config\resolution_N%%N.json" --branch stage_a_gauge_high || exit /b 1
  python -m sst_modal_clock.cli analyze-sciii-gauge "outputs\resolution_N%%N" "config\resolution_N%%N.json" || exit /b 1
)
python -m sst_modal_clock.cli resolution outputs\resolution_N64 outputs\resolution_N96 outputs\resolution_N128 outputs\RESOLUTION_SUMMARY.json || exit /b 1
