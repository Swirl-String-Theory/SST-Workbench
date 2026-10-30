@echo off
setlocal EnableExtensions
set "FW=%~dp0.."
if not defined SST_WORKBENCH_ROOT (
 echo ERROR: Set SST_WORKBENCH_ROOT to C:\workspace\projects\SST-Workbench
 exit /b 2
)
if not defined SST_PYTHON (
 echo ERROR: Set SST_PYTHON to the Python executable of the selected GPU environment.
 exit /b 2
)
if "%~1"=="" (
 echo Usage: run_a999_dd32_validation.cmd "C:\path\to\E010_export" [intel^|cuda]
 exit /b 2
)
if not exist "%~1\DATASET_MANIFEST.json" (
 echo ERROR: E010 export lacks DATASET_MANIFEST.json
 exit /b 2
)
set "PROVIDER=%~2"
if "%PROVIDER%"=="" set "PROVIDER=intel"
if /i not "%PROVIDER%"=="intel" if /i not "%PROVIDER%"=="cuda" (
 echo ERROR: Provider must be intel or cuda.
 exit /b 2
)
set "DEST=%TEMP%\A999_DD32_v111_%PROVIDER%_%RANDOM%_%RANDOM%"
if exist "%DEST%" (
 echo ERROR: create-only target already exists: %DEST%
 exit /b 2
)
cd /d "%FW%"
echo [DD32] Running local unit tests. GPU native compilation is checked below.
"%SST_PYTHON%" -m pytest -q tests
if errorlevel 1 exit /b 3
echo [DD32] Generating fresh E010 integration instance ...
"%SST_PYTHON%" "%FW%\tools\prepare_a999_e010.py" --dataset "%~1" --output "%DEST%" --gpu "%PROVIDER%" --precision dd32
if errorlevel 1 exit /b 4
echo [DD32] Probing native DD32 worker and C++ backend ...
call "%DEST%\run_all.cmd" BACKEND_PREFLIGHT
if errorlevel 1 exit /b 5
echo [DD32] FREEZE: untested native worker must not silently fall back to FP32.
call "%DEST%\run_all.cmd" FREEZE
if errorlevel 1 exit /b 6
echo [DD32] FULL, including actual native DD32 backend and numerical gate ...
call "%DEST%\run_all.cmd" FULL
if errorlevel 1 exit /b 7
echo [DD32] Auditing outputs, result hashes and G10 ...
"%SST_PYTHON%" "%FW%\tools\verify_a999_release.py" --instance "%DEST%" --output "%DEST%.acceptance.json"
if errorlevel 1 exit /b 8
echo [DD32] Development integration control completed. Inspect AUTO_BACKEND_MATRIX.json for precision dd32-fp32x2.
echo [DD32] Instance: %DEST%
echo [DD32] Acceptance: %DEST%.acceptance.json
exit /b 0
