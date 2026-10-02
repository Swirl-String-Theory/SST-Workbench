@echo off
setlocal
set DATA=%~1
if "%DATA%"=="" set DATA=..\..\KnotPlot\knots\final
call run_setup.cmd || exit /b 1
call run_build_native.cmd || exit /b 1
call run_selftest.cmd || exit /b 1
set OUT=outputs\relaxed_only
if exist "%OUT%" rmdir /s /q "%OUT%"
call .venv\Scripts\activate.bat || exit /b 1
python -m sst_modal_clock.cli prepare "%DATA%" "%OUT%" config\basic.json || exit /b 1
python -m sst_modal_clock.cli run "%OUT%" config\basic.json --branch stage_a || exit /b 1
python -m sst_modal_clock.cli analyze-sc2-stage-a "%OUT%" config\basic.json || exit /b 1
