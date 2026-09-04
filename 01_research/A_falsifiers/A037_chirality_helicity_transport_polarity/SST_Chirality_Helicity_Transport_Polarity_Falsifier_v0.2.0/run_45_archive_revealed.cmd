@echo off
setlocal
cd /d "%~dp0"
set OUT=%~1
if "%OUT%"=="" (
  echo Usage: run_45_archive_revealed.cmd outputs\basic_YYYYMMDD_HHMMSS
  exit /b 2
)
if not exist "%OUT%\REPORT_REVEALED.md" (
  echo ERROR: REPORT_REVEALED.md missing. Run reveal first.
  exit /b 1
)
if not exist archives mkdir archives
for %%I in ("%OUT%") do set NAME=%%~nxI
set ZIP=archives\%NAME%_REVEALED.zip
powershell -NoProfile -Command "Compress-Archive -Path '%OUT%\*' -DestinationPath '%ZIP%' -Force" || exit /b 1
echo Revealed archive: %ZIP%
exit /b 0
