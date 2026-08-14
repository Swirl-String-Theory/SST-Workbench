@echo off
setlocal EnableExtensions
pushd "%~dp0"
call "%~dp0_common.cmd" || goto :fail
"%PYTHON_EXE%" run_campaign.py --config configs\standard.json --input-root "%SST_KNOT_DIR%" || goto :fail
popd
exit /b 0
:fail
popd
exit /b 1
