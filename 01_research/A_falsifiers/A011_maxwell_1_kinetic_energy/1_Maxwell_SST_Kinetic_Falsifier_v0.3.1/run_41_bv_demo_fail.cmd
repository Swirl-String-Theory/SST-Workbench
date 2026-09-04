@echo off
setlocal
call "%~dp0_common.cmd" || exit /b 1
pushd "%~dp0"
if exist "outputs\bv_demo_fail" rmdir /s /q "outputs\bv_demo_fail"
"%PYTHON_EXE%" -m maxwell_sst_falsifier run --config "examples\bv_synthetic_fail\config.json" --out "outputs\bv_demo_fail"
set ERR=%errorlevel%
if not "%ERR%"=="0" goto :fail
echo.
echo [OK] Boltzmann-Verlinde synthetic FAIL audit complete.
echo      Inspect expected research-closure failures in:
echo      %CD%\outputs\bv_demo_fail\report.md
popd
exit /b 0
:fail
echo [ERROR] Boltzmann-Verlinde FAIL demo failed.
popd
exit /b %ERR%
