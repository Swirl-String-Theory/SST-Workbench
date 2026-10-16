@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  set "TC_ARGS=ALL"
) else (
  set "TC_ARGS=%*"
)
where py >nul 2>nul
if not errorlevel 1 (
  py -3 -m triadic.runner %TC_ARGS%
) else (
  python -m triadic.runner %TC_ARGS%
)
if errorlevel 1 exit /b 1
endlocal
