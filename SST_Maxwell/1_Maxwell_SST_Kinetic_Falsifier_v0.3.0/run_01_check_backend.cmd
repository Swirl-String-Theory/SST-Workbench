@echo off
setlocal
call "%~dp0_common.cmd" || exit /b 1
pushd "%~dp0"
echo.
echo ============================================================
echo [1_MaxwellSST] Backend + synthetic smoke check
echo ============================================================
"%PYTHON_EXE%" -m maxwell_sst_falsifier backend --force-build
if errorlevel 1 goto :fail
if exist "outputs\smoke" rmdir /s /q "outputs\smoke"
"%PYTHON_EXE%" -m maxwell_sst_falsifier workflow --knots-dir "examples\synthetic_knots" --out "outputs\smoke" --preset basic --threads 2
if errorlevel 1 goto :fail
echo [OK] Smoke output: %CD%\outputs\smoke\workflow_summary.json
popd
exit /b 0
:fail
echo [ERROR] Backend/smoke check failed.
popd
exit /b 1
