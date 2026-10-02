@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo SST Hopf FULL C++ validation - quick + standard + parity + benchmark
echo ============================================================

echo [1/6] Environment
call "cmd\00_SETUP_VENV.cmd"
if errorlevel 1 goto :fail

echo [2/6] Strict native C++ build
call "cmd\01_BUILD_CPP.cmd"
if errorlevel 1 goto :fail

echo [3/6] Native-vs-Python parity
call "cmd\05_RUN_NATIVE_PARITY.cmd"
if errorlevel 1 goto :fail

echo [4/6] QUICK H0-H10 C++ chain
call "cmd\02_RUN_QUICK_CPP.cmd"
if errorlevel 1 goto :fail

echo [5/6] STANDARD H0-H10 C++ chain
call "cmd\03_RUN_STANDARD_CPP.cmd"
if errorlevel 1 goto :fail

echo [6/6] C++ versus Python timing benchmark
call "cmd\06_BENCHMARK_CPP_VS_PYTHON.cmd"
if errorlevel 1 goto :fail

echo ============================================================
echo PASS - full validation complete.
echo Results:
echo   results\native_selfcheck.json
echo   results\quick_cpp\run_summary.json
echo   results\standard_cpp\run_summary.json
echo   results\cpp_vs_python_benchmark.json
echo ============================================================
exit /b 0

:fail
echo ============================================================
echo FAIL - full validation stopped at the failing gate.
echo Inspect the console and the latest results\...\logs directory.
echo ============================================================
exit /b 1
