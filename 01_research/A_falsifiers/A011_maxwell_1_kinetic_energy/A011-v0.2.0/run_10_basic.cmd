@echo off
setlocal
call "%~dp0_common.cmd" || exit /b 1
if not exist "%SST_KNOT_DIR%" (
  echo [ERROR] Knot directory not found: %SST_KNOT_DIR%
  echo Edit: %~dp0config\paths.cmd
  exit /b 2
)
pushd "%~dp0"
echo.
echo ============================================================
echo [1_MaxwellSST] BASIC physical-geometry workflow
echo ============================================================
if exist "outputs\basic" rmdir /s /q "outputs\basic"
"%PYTHON_EXE%" -m maxwell_sst_falsifier workflow --knots-dir "%SST_KNOT_DIR%" --out "outputs\basic" --preset basic --threads %SST_NATIVE_THREADS%
if errorlevel 1 goto :fail
echo.
echo [OK] BASIC finished.
echo      %CD%\outputs\basic\README_RESULTS.md
echo      %CD%\outputs\basic\geometry_metrics.csv
echo      %CD%\outputs\basic\interaction_coupling_proxy.csv
popd
exit /b 0
:fail
echo [ERROR] BASIC run failed.
popd
exit /b 1
