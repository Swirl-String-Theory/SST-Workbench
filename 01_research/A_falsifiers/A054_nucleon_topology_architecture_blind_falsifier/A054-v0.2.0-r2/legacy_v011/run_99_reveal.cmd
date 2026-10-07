@echo off
setlocal
cd /d "%~dp0"
call .venv\Scripts\activate.bat
set "OUT=%~1"
if "%OUT%"=="" if exist LAST_CAMPAIGN.txt set /p OUT=<LAST_CAMPAIGN.txt
if "%OUT%"=="" exit /b 2
a054-ntaf reveal --campaign "%OUT%" || exit /b %errorlevel%
python tools\pack_outputs.py --campaign "%OUT%" --mode revealed || exit /b %errorlevel%
echo Revealed report: %OUT%\REPORT_REVEALED.md
exit /b 0
