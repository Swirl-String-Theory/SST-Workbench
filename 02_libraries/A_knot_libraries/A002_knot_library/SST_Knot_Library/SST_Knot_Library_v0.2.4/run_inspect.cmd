@echo off
setlocal
cd /d "%~dp0"
if "%~2"=="" (
  echo Usage: run_inspect.cmd ^<geometry-file^> ^<topology-id^> [core-radius]
  echo Example: run_inspect.cmd ..\..\KnotPlot\knots\final\6.2\ideal.txt 6_2 0.05
  exit /b 2
)
set "CR=%~3"
if "%CR%"=="" (
  .venv\Scripts\python.exe -m sst_knotlib inspect "%~1" --topology "%~2" --provider auto
) else (
  .venv\Scripts\python.exe -m sst_knotlib inspect "%~1" --topology "%~2" --provider auto --core-radius %CR%
)
exit /b %errorlevel%
