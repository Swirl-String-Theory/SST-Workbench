@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if not exist analysis\CERTIFICATION.json (
  echo ERROR: run certification analysis first.
  exit /b 2
)

if exist analysis\EXTENDED_SKIPPED.flag del /q analysis\EXTENDED_SKIPPED.flag >nul 2>nul

set "PARAMS="
for /f "usebackq delims=" %%P in (`python -c "import json; d=json.load(open(r'analysis\CERTIFICATION.json')); print(' '.join(d.get('certified_effective',[])))"`) do set "PARAMS=%%P"

if "%PARAMS%"=="" (
  echo No parameters certified effective. Extended stage skipped.
  >analysis\EXTENDED_SKIPPED.flag echo No parameters certified effective.
  exit /b 0
)

echo Certified parameters: %PARAMS%
python run_knotplot_stage.py --stage extended --params %PARAMS%
exit /b %ERRORLEVEL%
