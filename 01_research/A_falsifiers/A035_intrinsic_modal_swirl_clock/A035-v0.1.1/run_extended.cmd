@echo off
setlocal
set DATA=%~1
if "%DATA%"=="" set DATA=..\..\KnotPlot\knots\final
set OUT=outputs\extended
if exist "%OUT%" rmdir /s /q "%OUT%"
call .venv\Scripts\activate.bat
python -m sst_modal_clock.cli prepare "%DATA%" "%OUT%" config\extended.json || exit /b 1
python -m sst_modal_clock.cli run "%OUT%" config\extended.json --branch material || exit /b 1
python -m sst_modal_clock.cli run "%OUT%" config\extended.json --branch fixed || exit /b 1
python -m sst_modal_clock.cli analyze "%OUT%" config\extended.json || exit /b 1
echo Blind result: %OUT%\analysis\blind_summary.json
