@echo off
setlocal EnableExtensions
set "FW=%~dp0.."
if not defined SST_WORKBENCH_ROOT (
  echo ERROR: Set SST_WORKBENCH_ROOT to C:\workspace\projects\SST-Workbench
  exit /b 2
)
if not defined SST_PYTHON (
  echo ERROR: Set SST_PYTHON to your Python 3.14 Intel-XPU python.exe
  exit /b 2
)
if "%~1"=="" (
  echo Usage: run_a999_rc2_acceptance.cmd "C:\path\to\verified_E010_export"
  exit /b 2
)
if not exist "%~1\DATASET_MANIFEST.json" (
  echo ERROR: Provided E010 export lacks DATASET_MANIFEST.json
  exit /b 2
)
set "DEST=%TEMP%\A999_E010_RC2_%RANDOM%_%RANDOM%"
if exist "%DEST%" (
  echo ERROR: create-only destination exists: %DEST%
  exit /b 2
)
cd /d "%FW%"
echo [RC2] Checking complete release test suite ...
"%SST_PYTHON%" -m pytest -q tests
if errorlevel 1 exit /b 3
echo [RC2] Preparing a new frozen local A999 ...
"%SST_PYTHON%" "%FW%\tools\prepare_a999_e010.py" --dataset "%~1" --output "%DEST%" --gpu intel
if errorlevel 1 exit /b 4
echo [RC2] Preflight hardware ...
call "%DEST%\run_all.cmd" BACKEND_PREFLIGHT
if errorlevel 1 exit /b 5
echo [RC2] Freezing scientific numeric control ...
call "%DEST%\run_all.cmd" FREEZE
if errorlevel 1 exit /b 6
echo [RC2] Executing; heartbeat every 15s, each backend announces progress ...
call "%DEST%\run_all.cmd" FULL
if errorlevel 1 exit /b 7
echo [RC2] Auditing independent scientific evidence, progress journal, PDF, ZIP ...
"%SST_PYTHON%" "%FW%\tools\verify_a999_release.py" --instance "%DEST%" --output "%DEST%.acceptance.json"
if errorlevel 1 exit /b 8
echo [RC2] PASS_TECHNICAL_INTEGRATION_ONLY - no physical SST claims.
echo [RC2] Instance: %DEST%
echo [RC2] Acceptance: %DEST%.acceptance.json
exit /b 0
