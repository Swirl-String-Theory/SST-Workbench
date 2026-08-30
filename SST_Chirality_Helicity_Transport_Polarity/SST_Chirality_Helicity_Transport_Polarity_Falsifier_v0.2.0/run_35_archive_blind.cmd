@echo off
setlocal
cd /d "%~dp0"
set OUT=%~1
if "%OUT%"=="" (
  echo Usage: run_35_archive_blind.cmd outputs\basic_YYYYMMDD_HHMMSS
  exit /b 2
)
if not exist "%OUT%\BLIND_SEAL.json" (
  echo ERROR: BLIND_SEAL.json missing. Run blind analysis first.
  exit /b 1
)
if not exist archives mkdir archives
for %%I in ("%OUT%") do set NAME=%%~nxI
set ZIP=archives\%NAME%_BLIND.zip
powershell -NoProfile -Command "Compress-Archive -Path '%OUT%\*' -DestinationPath '%ZIP%' -Force" || exit /b 1
echo Blind archive: %ZIP%
echo Private reveal mapping is NOT inside this ZIP.
exit /b 0
