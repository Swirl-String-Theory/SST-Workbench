@echo off
setlocal
set "DATASET=%~1"
if "%DATASET%"=="" set "DATASET=..\..\KnotPlot\knots\final"
set OMP_NUM_THREADS=%NUMBER_OF_PROCESSORS%
call .venv\Scripts\activate.bat
for %%N in (64 96 128) do (
  echo ============================================================
  echo Resolution N=%%N
  echo ============================================================
  python -m sst_bsrp_falsifier.cli prepare "%DATASET%" "outputs\resolution_N%%N" "config\resolution_N%%N.json" || goto :fail
  python -m sst_bsrp_falsifier.cli run "outputs\resolution_N%%N" "config\resolution_N%%N.json" || goto :fail
  python -m sst_bsrp_falsifier.cli analyze "outputs\resolution_N%%N" "config\resolution_N%%N.json" || goto :fail
)
python -m sst_bsrp_falsifier.cli resolution outputs\resolution_N64 outputs\resolution_N96 outputs\resolution_N128 outputs\resolution_summary.json || goto :fail
echo Resolution summary: outputs\resolution_summary.json
exit /b 0
:fail
exit /b 1
