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
echo [1_MaxwellSST] EXTENDED self-pair workflow - C++ backend required
echo ============================================================
if exist "outputs\extended" rmdir /s /q "outputs\extended"
"%PYTHON_EXE%" -m maxwell_sst_falsifier workflow --knots-dir "%SST_KNOT_DIR%" --out "outputs\extended" --preset extended --pairing self --threads %SST_NATIVE_THREADS% --require-native
if errorlevel 1 goto :fail
echo.
echo [OK] EXTENDED finished.
echo      %CD%\outputs\extended\README_RESULTS.md
echo      %CD%\outputs\extended\interaction_coupling_proxy.csv
popd
exit /b 0
:fail
echo [ERROR] EXTENDED run failed. If native C++ is unavailable, run run_00_install.cmd first.
popd
exit /b 1
