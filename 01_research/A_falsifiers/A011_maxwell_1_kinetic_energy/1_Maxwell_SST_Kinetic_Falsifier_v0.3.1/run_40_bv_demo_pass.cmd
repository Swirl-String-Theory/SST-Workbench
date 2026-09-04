@echo off
setlocal
call "%~dp0_common.cmd" || exit /b 1
pushd "%~dp0"
if exist "outputs\bv_demo_pass" rmdir /s /q "outputs\bv_demo_pass"
"%PYTHON_EXE%" -m maxwell_sst_falsifier run --config "examples\bv_synthetic_pass\config.json" --out "outputs\bv_demo_pass"
set ERR=%errorlevel%
if not "%ERR%"=="0" goto :fail
echo.
echo [OK] Boltzmann-Verlinde synthetic PASS audit complete.
echo      %CD%\outputs\bv_demo_pass\report.md
popd
exit /b 0
:fail
echo [ERROR] Boltzmann-Verlinde PASS demo failed.
popd
exit /b %ERR%
