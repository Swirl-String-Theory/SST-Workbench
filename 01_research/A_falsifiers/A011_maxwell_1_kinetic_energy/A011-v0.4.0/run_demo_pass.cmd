@echo off
setlocal
call "%~dp0_common.cmd" || exit /b 1
pushd "%~dp0"
if exist "outputs\synthetic_pass" rmdir /s /q "outputs\synthetic_pass"
"%PYTHON_EXE%" -m maxwell_sst_falsifier run --config "examples\synthetic_pass\config.json" --out "outputs\synthetic_pass"
set ERR=%errorlevel%
popd
exit /b %ERR%
