@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
set OUT=SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier_v0.3.3-outputs\validation
if not exist "%OUT%" mkdir "%OUT%"
"%PY%" -m sst_seed_falsifier.remap_benchmark --out "%OUT%\remap_kernel_benchmark_v0.3.3.json" %*
if errorlevel 1 exit /b 1
endlocal

REM Add --smoke for the short non-certifying Python diagnostic.
