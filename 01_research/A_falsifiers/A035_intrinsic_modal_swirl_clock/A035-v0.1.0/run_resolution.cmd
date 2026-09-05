@echo off
setlocal
set DATA=%~1
if "%DATA%"=="" set DATA=..\..\KnotPlot\knots\final
call .venv\Scripts\activate.bat
for %%N in (64 96 128) do (
  set OUT=outputs\resolution_N%%N
  if exist "outputs\resolution_N%%N" rmdir /s /q "outputs\resolution_N%%N"
  python -m sst_modal_clock.cli prepare "%DATA%" "outputs\resolution_N%%N" "config\resolution_N%%N.json" || exit /b 1
  python -m sst_modal_clock.cli run "outputs\resolution_N%%N" "config\resolution_N%%N.json" --branch material || exit /b 1
  python -m sst_modal_clock.cli run "outputs\resolution_N%%N" "config\resolution_N%%N.json" --branch fixed || exit /b 1
  python -m sst_modal_clock.cli analyze "outputs\resolution_N%%N" "config\resolution_N%%N.json" || exit /b 1
)
python -m sst_modal_clock.cli resolution outputs\resolution_N64 outputs\resolution_N96 outputs\resolution_N128 outputs\RESOLUTION_SUMMARY.json || exit /b 1
