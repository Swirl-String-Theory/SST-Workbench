@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo SST Hopf H0-H10 one-click C++/pybind run

echo [1/4] Environment
if not exist ".venv\Scripts\python.exe" call "cmd\00_SETUP_VENV.cmd"
if errorlevel 1 goto :fail

echo [SST-HOPF] Dependency audit
.venv\Scripts\python.exe run_dependency_preflight.py
if errorlevel 1 goto :fail
echo [2/4] Native C++ build
call "cmd\01_BUILD_CPP.cmd"
if errorlevel 1 goto :fail

echo [3/4] C++/Python parity
call "cmd\05_RUN_NATIVE_PARITY.cmd"
if errorlevel 1 goto :fail

echo [4/4] Standard H0-H10 chain
call "cmd\03_RUN_STANDARD_CPP.cmd"
if errorlevel 1 goto :fail

echo ============================================================
echo PASS - see results\standard_cpp\run_summary.json
exit /b 0
:fail
echo ============================================================
echo FAIL - inspect the last printed error and results logs.
exit /b 1
