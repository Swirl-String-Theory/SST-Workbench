@echo off
setlocal

set PRESET=%1

if "%PRESET%"=="" (
    set PRESET=quick
)

echo.
echo ==============================================
echo SST Chiral Kelvin Falsification v0.1.2.1
echo Preset: %PRESET%
echo ==============================================
echo.

echo [1/2] Building/checking native pybind extension...
python -m chiral_kelvin.build_ext_if_needed --strict

if errorlevel 1 (
    echo.
    echo ERROR: native build failed.
    exit /b 1
)

echo.
echo [2/2] Running audit and convergence ladder...

python run_all_checks.py ^
    --preset %PRESET% ^
    --out-dir audit_out_v0121

set RC=%errorlevel%

echo.
echo ==============================================
echo Finished with exit code %RC%
echo Results: audit_out_v0121
echo ==============================================
echo.

exit /b %RC%
