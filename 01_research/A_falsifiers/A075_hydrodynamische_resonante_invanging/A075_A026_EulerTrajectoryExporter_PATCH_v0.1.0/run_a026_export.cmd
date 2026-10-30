@echo off
setlocal EnableExtensions
if "%~1"=="" (
  echo Usage: run_a026_export.cmd "C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A075_Hydrodynamische_Resonante_Invanging\A075-v0.2.9" [extra flags]
  echo Optional smoke: --trials 4 --mode legacy_t23 --grid 16
  exit /b 2
)
set "A075_ROOT=%~1"
shift
set "EXTRA_ARGS="
:nextarg
if "%~1"=="" goto run
set EXTRA_ARGS=%EXTRA_ARGS% %1
shift
goto nextarg
:run
py -3 "%~dp0export_a026_trajectories.py" --a075-root "%A075_ROOT%" %EXTRA_ARGS%
exit /b %errorlevel%
