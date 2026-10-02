@echo off
setlocal EnableExtensions
if "%~1"=="" (echo Usage: run_90_pack_blind.cmd path\to\frozen_run_directory& exit /b 2)
set "OUT=%~f1"
if not exist "%OUT%\FROZEN_SHA256.json" (echo ERROR: FROZEN_SHA256.json missing. Refusing to pack.& exit /b 3)
for %%I in ("%OUT%") do set "NAME=%%~nxI"
set "ZIP=%~dp0..\3_Maxwell_SST_Physical_Lines_Falsifier_v0.3.0_%NAME%_BLIND.zip"
if exist "%ZIP%" del /q "%ZIP%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Path '%OUT%\*' -DestinationPath '%ZIP%' -CompressionLevel Optimal"
if errorlevel 1 exit /b %errorlevel%
echo [3_MAXWELL] BLIND archive: %ZIP%
exit /b 0
