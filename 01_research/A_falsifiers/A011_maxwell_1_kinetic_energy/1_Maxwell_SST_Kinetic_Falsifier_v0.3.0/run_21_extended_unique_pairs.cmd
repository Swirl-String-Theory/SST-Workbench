@echo off
setlocal
call "%~dp0_common.cmd" || exit /b 1
if not exist "%SST_KNOT_DIR%" (
  echo [ERROR] Knot directory not found: %SST_KNOT_DIR%
  exit /b 2
)
pushd "%~dp0"
echo.
echo ============================================================
echo [1_MaxwellSST] EXTENDED UNIQUE-PAIR campaign - potentially expensive
echo ============================================================
if exist "outputs\extended_unique_pairs" rmdir /s /q "outputs\extended_unique_pairs"
"%PYTHON_EXE%" -m maxwell_sst_falsifier workflow --knots-dir "%SST_KNOT_DIR%" --out "outputs\extended_unique_pairs" --preset extended --pairing unique --threads %SST_NATIVE_THREADS% --require-native
if errorlevel 1 goto :fail
echo [OK] Unique-pair campaign finished.
popd
exit /b 0
:fail
echo [ERROR] Unique-pair campaign failed.
popd
exit /b 1
