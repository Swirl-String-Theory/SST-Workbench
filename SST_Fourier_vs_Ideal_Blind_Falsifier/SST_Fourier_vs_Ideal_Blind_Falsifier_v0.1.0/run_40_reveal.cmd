@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
call _common.cmd || exit /b 1
set "BLIND=%~1"
if "%BLIND%"=="" (
  for /f "delims=" %%D in ('dir /b /ad /o-d outputs\blind_* 2^>nul ^| findstr /v /i "revealed"') do if not defined BLIND set "BLIND=outputs\%%D"
)
if "%BLIND%"=="" (echo Usage: run_40_reveal.cmd outputs\blind_xxx & exit /b 2)
set "CFG=config\preset_torus.json"
echo %BLIND% | findstr /i "extended" >nul && set "CFG=config\preset_extended.json"
echo %BLIND% | findstr /i "relaxed_control" >nul && set "CFG=config\preset_relaxed_control.json"
set "OUT=%BLIND%_revealed"
"%PY%" -m sst_fourier_ideal_falsifier.cli reveal --project-root . --blind "%BLIND%" --catalog blind_catalog --config "!CFG!" --private private --out "%OUT%"
if errorlevel 1 exit /b 1
echo [SST-FVI] REVEAL: %OUT%
exit /b 0
