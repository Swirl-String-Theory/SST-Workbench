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
echo Usage: run_42_bv_physical.cmd ^<physical_campaign\config.json^> ^<outdir^>
echo.
echo The same strict campaign engine evaluates Maxwell kinetic gates plus any
 echo preregistered Boltzmann/Verlinde research_claims whose CSV inputs are present.
exit /b 2
