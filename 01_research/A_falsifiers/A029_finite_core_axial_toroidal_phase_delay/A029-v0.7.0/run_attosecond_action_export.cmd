@echo off
setlocal
cd /d "%~dp0"
call "%~dp0_common.cmd" || exit /b 1
if "%~1"=="" (
  echo Usage: run_attosecond_action_export.cmd ^<contract.json^> [output_dir]
  exit /b 2
)
set "OUT=%~2"
if "%OUT%"=="" set "OUT=outputs\attosecond_action"
"%PY%" -m sst_finite_core_falsifier.cli attosecond-action-export --input "%~1" --out "%OUT%" --config config\preset_attosecond_action_export.json
exit /b %errorlevel%
