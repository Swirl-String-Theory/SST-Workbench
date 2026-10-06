@echo off
setlocal
cd /d "%~dp0"
call .venv\Scripts\activate.bat
set "OUT=%~1"
if "%OUT%"=="" if exist LAST_CAMPAIGN.txt set /p OUT=<LAST_CAMPAIGN.txt
if "%OUT%"=="" exit /b 2
a054-ntaf reveal --campaign "%OUT%" || exit /b %errorlevel%
python -c "import shutil,sys,pathlib; p=pathlib.Path(sys.argv[1]); shutil.make_archive(str(p)+'_REVEALED','zip',p)" "%OUT%"
echo Revealed report: %OUT%\REPORT_REVEALED.md
exit /b 0
