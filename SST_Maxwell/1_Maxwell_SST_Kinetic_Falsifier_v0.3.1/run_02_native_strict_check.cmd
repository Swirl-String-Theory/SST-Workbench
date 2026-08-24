@echo off
setlocal
call "%~dp0_common.cmd" || exit /b 1
pushd "%~dp0"
echo.
echo ============================================================
echo [1_MaxwellSST] STRICT native C++ backend check
echo ============================================================
"%PYTHON_EXE%" -m maxwell_sst_falsifier backend --require-native
if errorlevel 1 goto :fail
echo [OK] Native C++ backend is active.
popd
exit /b 0
:fail
echo [ERROR] Native backend unavailable. See compiler output above.
popd
exit /b 1
