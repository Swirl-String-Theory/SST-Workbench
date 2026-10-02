@echo off
setlocal

set PRESET=%1

if "%PRESET%"=="" (
    set PRESET=quick
)

echo.
echo ============================================
echo SST Chiral Kelvin falsification v0.1.2
echo preset = %PRESET%
echo ============================================
echo.

python -m chiral_kelvin.build_ext_if_needed --force --strict

if errorlevel 1 (
    echo Native build FAILED.
    exit /b 1
)

python run_all_checks.py ^
    --preset %PRESET% ^
    --out-dir audit_out_v012 ^
    --force-build

set RC=%errorlevel%

echo.
echo Results:
echo     audit_out_v012
echo.

exit /b %RC%
