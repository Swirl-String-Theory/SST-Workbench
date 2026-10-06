@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
    echo [ERROR] .venv is missing. Run run_build_cpp.cmd first.
    exit /b 20
)
if not exist build (
    echo [ERROR] build directory is missing. Run run_build_cpp.cmd first.
    exit /b 21
)
.venv\Scripts\python.exe tools\stage_native_runtime.py
if errorlevel 1 exit /b 22
.venv\Scripts\python.exe tools\native_parity.py
if errorlevel 1 exit /b 23
exit /b 0
