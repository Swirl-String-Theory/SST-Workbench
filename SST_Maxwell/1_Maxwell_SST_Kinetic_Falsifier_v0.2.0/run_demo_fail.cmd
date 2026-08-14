@echo off
setlocal
call "%~dp0_common.cmd" || exit /b 1
pushd "%~dp0"
if exist "outputs\synthetic_fail" rmdir /s /q "outputs\synthetic_fail"
"%PYTHON_EXE%" -m maxwell_sst_falsifier run --config "examples\synthetic_fail\config.json" --out "outputs\synthetic_fail"
set ERR=%errorlevel%
popd
exit /b %ERR%
