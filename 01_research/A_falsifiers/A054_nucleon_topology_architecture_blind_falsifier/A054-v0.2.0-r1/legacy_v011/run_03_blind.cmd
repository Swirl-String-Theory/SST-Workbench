@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
call .venv\Scripts\activate.bat
set "OUT=%~1"
if "!OUT!"=="" if exist LAST_CAMPAIGN.txt set /p OUT=<LAST_CAMPAIGN.txt
if "!OUT!"=="" (echo No campaign path. & exit /b 2)
if not exist "!OUT!\blind_runner\run_blind.py" python tools\build_blind_runner.py --campaign "!OUT!" || exit /b !errorlevel!
python "!OUT!\blind_runner\run_blind.py" --campaign "!OUT!" --config configs\basic.json
if errorlevel 1 exit /b !errorlevel!
echo Blind report: !OUT!\REPORT_BLIND.md
echo Reveal only after inspecting/freezing the blind report: run_99_reveal.cmd "!OUT!"
exit /b 0
