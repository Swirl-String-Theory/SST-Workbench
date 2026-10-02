@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call "_RESOLVE_INPUT.cmd" "%~1"
set "RC=%ERRORLEVEL%"
if "%RC%"=="0" (
  echo.
  echo INPUT RESOLUTION PASS
  echo %INPUT%
) else (
  echo.
  echo INPUT RESOLUTION FAILED with exit code %RC%.
)
exit /b %RC%
