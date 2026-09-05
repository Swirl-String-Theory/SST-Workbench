@echo off
setlocal
call "%~dp0_common.cmd" || exit /b 1
if "%~1"=="" goto :usage
if "%~2"=="" goto :usage
pushd "%~dp0"
"%PYTHON_EXE%" -m maxwell_sst_falsifier run --config "%~1" --out "%~2"
set ERR=%errorlevel%
popd
exit /b %ERR%
:usage
echo Usage: run_30_physical_falsifier.cmd ^<config.json^> ^<outdir^>
echo.
echo IMPORTANT: use this only after the v01_physical_campaign_skeleton CSVs
echo have been populated with PHYSICAL solver/experimental energies, gaps and times.
exit /b 2
