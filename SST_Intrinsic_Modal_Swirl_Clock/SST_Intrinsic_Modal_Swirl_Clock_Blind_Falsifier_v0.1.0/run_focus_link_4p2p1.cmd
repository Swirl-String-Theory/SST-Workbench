@echo off
setlocal
set DATA=%~1
if "%DATA%"=="" set DATA=..\..\KnotPlot\knots\final
set OUT=outputs\focus_link_4p2p1
if exist "%OUT%" rmdir /s /q "%OUT%"
call .venv\Scripts\activate.bat
python -m sst_modal_clock.cli prepare "%DATA%" "%OUT%" config\focus_link_4p2p1.json || exit /b 1
python -m sst_modal_clock.cli run "%OUT%" config\focus_link_4p2p1.json --branch material || exit /b 1
python -m sst_modal_clock.cli run "%OUT%" config\focus_link_4p2p1.json --branch fixed || exit /b 1
python -m sst_modal_clock.cli analyze "%OUT%" config\focus_link_4p2p1.json || exit /b 1
