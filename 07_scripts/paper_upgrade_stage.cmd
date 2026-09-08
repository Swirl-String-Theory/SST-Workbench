@echo off
rem Thin wrapper: paper_upgrade_stage.cmd <family> <tier> <out> <stage_id> <command...>
rem Resolves 07_scripts/paper_upgrade_runtime.py relative to this file.
setlocal EnableExtensions
set "FAM=%~1"
set "TIER=%~2"
set "OUTDIR=%~3"
set "SID=%~4"
if "%FAM%"=="" (
  echo usage: paper_upgrade_stage.cmd family tier out stage_id command...
  exit /b 2
)
shift
shift
shift
shift
set "WB=%~dp0.."
set "PY=python"
if defined SST_PYTHON set "PY=%SST_PYTHON%"
set "RESUME_FLAG="
if /I "%SST_RESUME%"=="1" set "RESUME_FLAG=--resume"
"%PY%" "%~dp0paper_upgrade_runtime.py" stage --family "%FAM%" --tier "%TIER%" --out "%OUTDIR%" --id "%SID%" %RESUME_FLAG% -- %*
exit /b %ERRORLEVEL%
